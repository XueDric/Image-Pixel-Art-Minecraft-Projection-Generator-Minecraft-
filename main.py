# -*- coding: utf-8 -*-
"""
main.py —— 图片 → 像素画 → Minecraft 投影 生成器（图形界面）

支持 中文 / English 两种界面语言（控制面板顶部切换，实时生效）。

流水线：
    ① 选择图片 → 选择像素尺寸（16×16 ~ 4096×4096 / 自定义 / 保持宽高比）
    ② 生成像素画（保留原色，可选去除背景）
    ③ 生成MC投影（MC 方块调色板匹配 → .litematic + 预览图 + 方块用量CSV）

运行：python main.py
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

import pipeline
import pixelart2litematic
import i18n

APP_TITLE = "图片 → 像素画 → Minecraft投影 生成器"

# ---------- 阶段1 ----------
SIZE_PRESETS = pipeline.SIZE_PRESETS
MAX_DIM = pipeline.MAX_DIM
CELL_SIZES = [1, 2, 4, 8, 10, 12, 16, 20, 24, 32]
DEFAULT_CELL = 16
MAX_PREVIEW_PX = 4096

# ---------- 阶段2 ----------
MC_PALETTE_VALUES = pipeline.MC_PALETTE_VALUES
DITHER_VALUES = pipeline.DITHER_VALUES
MC_CELL_SIZES = [4, 8, 12, 14, 16, 20, 24, 32]
DEFAULT_MC_CELL = 14

# ---------- 语言无关的选项：id -> (中文标签, English 标签) ----------
# 顺序必须与 pipeline.MC_PALETTE_VALUES / DITHER_VALUES / "none/trim/glass" 一致
BG_OPTIONS = [
    ("none", "无", "None"),
    ("trim", "去除背景(镂空)", "Remove background (carve-out)"),
    ("glass", "背景填玻璃", "Glass background"),
]
PALETTE_OPTIONS = [
    ("auto", "auto（全部149种）", "auto (all 149)"),
    ("wool", "wool（羊毛）", "wool"),
    ("concrete", "concrete（混凝土）", "concrete"),
    ("terracotta", "terracotta（陶瓦）", "terracotta"),
    ("glass", "glass（玻璃）", "glass"),
    ("wool+concrete", "wool+concrete", "wool+concrete"),
    ("concrete+terracotta", "concrete+terracotta", "concrete+terracotta"),
    ("misc", "misc（建材）", "misc (blocks)"),
]
DITHER_OPTIONS = [
    ("floyd", "floyd（抖动，渐变平滑）", "floyd (dithered)"),
    ("none", "none（纯色）", "none (solid)"),
]


def dpi_aware():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.lang = "zh"                 # "zh" / "en"
        self._text_widgets = []          # [(widget, zh_text), ...]
        self._combos = []                # [(StringVar, spec, combobox), ...]
        root.title(i18n.tr(APP_TITLE, self.lang))
        root.geometry("1280x760")
        root.minsize(1080, 680)

        self.q = queue.Queue()
        self.worker = None

        # 状态
        self.original_image = None      # PIL RGB
        self.image_path = None
        self.stage1 = None              # pipeline.Stage1Result
        self.stage2 = None              # run_stage2 结果字典
        self.bg_color = None            # (r,g,b)；None=自动白色
        self._photo_refs = []           # 防止 PhotoImage 被 GC
        self.last_out_dir = None

        self._build_ui()
        root.after(100, self._poll_queue)

    # ------------------------------------------------------------ 文案
    def _t(self, zh):
        """静态文案：按当前语言返回。"""
        return i18n.tr(zh, self.lang)

    def _pick(self, zh, en):
        """动态文案：按当前语言二选一。"""
        return en if self.lang == "en" else zh

    def _tfmt(self, zh, en, **kw):
        """动态文案 + 格式化。"""
        return (en if self.lang == "en" else zh).format(**kw)

    def _reg(self, widget, zh):
        """登记一个带文本的控件，语言切换时统一更新。"""
        self._text_widgets.append((widget, zh))
        return widget

    # ------------------------------------------------------------ UI 助手
    def _make_label(self, parent, text, **kw):
        return self._reg(ttk.Label(parent, text=self._t(text), **kw), text)

    def _make_button(self, parent, text, command):
        return self._reg(ttk.Button(parent, text=self._t(text), command=command), text)

    def _make_check(self, parent, text, variable, command=None):
        return self._reg(ttk.Checkbutton(parent, text=self._t(text),
                                         variable=variable, command=command), text)

    def _make_radio(self, parent, text, variable, value):
        return self._reg(ttk.Radiobutton(parent, text=self._t(text),
                                         variable=variable, value=value), text)

    def _spec_values(self, spec):
        return [self._t(zh) for _, zh, _en in spec]

    def _combo_id(self, spec, variable):
        label = variable.get()
        for cid, zh, en in spec:
            if label == zh or label == en:
                return cid
        return spec[0][0]

    def _combo_label(self, spec, cid):
        for c, zh, _en in spec:
            if c == cid:
                return self._t(zh)
        return ""

    def _size_values(self):
        return [p if p != "自定义" else self._t("自定义") for p in SIZE_PRESETS]

    def _set_lang(self, lang):
        if lang == self.lang:
            return
        self.lang = lang
        self._apply_lang()
        self.refresh_pixel_preview()
        self.refresh_mc_preview()

    def _apply_lang(self):
        self.root.title(self._t(APP_TITLE))
        for widget, zh in self._text_widgets:
            try:
                widget.configure(text=self._t(zh))
            except Exception:
                pass
        for var, spec, combo in self._combos:
            cid = self._combo_id(spec, var)
            combo.configure(values=self._spec_values(spec))
            var.set(self._combo_label(spec, cid))
        # 尺寸下拉（特殊：除“自定义”外均为数字）
        try:
            sel = self.size_var.get()
            self.size_combo.configure(values=self._size_values())
            if sel in ("自定义", "Custom"):
                self.size_var.set(self._t("自定义"))
        except Exception:
            pass

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        pad = {"padx": 6, "pady": 3}

        bar = self._reg(ttk.LabelFrame(self.root, text=self._t("控制面板")), "控制面板")
        bar.pack(fill="x", padx=8, pady=6)

        # ---- 行L：语言 ----
        lang_row = ttk.Frame(bar)
        lang_row.pack(fill="x", **pad)
        self._make_label(lang_row, "语言:").pack(side="left")
        lv = tk.StringVar(value=self.lang)
        for lang_id, label in (("zh", "中文"), ("en", "English")):
            ttk.Radiobutton(lang_row, text=label, variable=lv, value=lang_id,
                            command=lambda: self._set_lang(lv.get())).pack(side="left", padx=4)

        # ---- 行0：图片 / 输出目录 ----
        row0 = ttk.Frame(bar)
        row0.pack(fill="x", **pad)
        self._make_button(row0, "① 选择图片...", self.choose_image).pack(side="left")
        self.file_label = self._make_label(row0, "未选择图片", foreground="#888")
        self.file_label.pack(side="left", padx=8)
        self._make_label(row0, "输出目录:").pack(side="left", padx=(16, 0))
        self.outdir_var = tk.StringVar()
        ttk.Entry(row0, textvariable=self.outdir_var, width=28).pack(side="left", padx=4)
        self._make_button(row0, "选择…", self.pick_outdir).pack(side="left")

        # ---- 行1：阶段1 尺寸 ----
        row1 = ttk.Frame(bar)
        row1.pack(fill="x", **pad)
        self._make_label(row1, "阶段1 像素尺寸:").pack(side="left")
        self.size_var = tk.StringVar(value=SIZE_PRESETS[3])   # 默认 48×48
        self.size_combo = ttk.Combobox(row1, textvariable=self.size_var,
                                       values=SIZE_PRESETS, state="readonly", width=8)
        self.size_combo.pack(side="left", padx=4)
        self.size_combo.bind("<<ComboboxSelected>>", self._on_size_change)

        self.custom_w = tk.IntVar(value=64)
        self.custom_h = tk.IntVar(value=48)
        self.custom_frame = ttk.Frame(row1)
        self.custom_frame.pack(side="left", padx=4)
        self._make_label(self.custom_frame, "宽:").pack(side="left")
        ttk.Spinbox(self.custom_frame, from_=1, to=MAX_DIM, width=4,
                    textvariable=self.custom_w).pack(side="left")
        self._make_label(self.custom_frame, "高:").pack(side="left", padx=(6, 0))
        ttk.Spinbox(self.custom_frame, from_=1, to=MAX_DIM, width=4,
                    textvariable=self.custom_h).pack(side="left")
        self.custom_frame.pack_forget()

        self.keep_aspect_var = tk.BooleanVar(value=False)
        self.keep_aspect_check = self._make_check(row1, "保持宽高比", self.keep_aspect_var)
        self.keep_aspect_check.pack(side="left", padx=8)

        # ---- 行2：阶段1 背景处理 / 生成按钮 ----
        row2 = ttk.Frame(bar)
        row2.pack(fill="x", **pad)
        self._make_label(row2, "背景处理:").pack(side="left")
        self.bg_mode_var = tk.StringVar(value=self._t(BG_OPTIONS[0][1]))
        bg_combo = ttk.Combobox(row2, textvariable=self.bg_mode_var,
                                state="readonly", width=16,
                                values=self._spec_values(BG_OPTIONS))
        bg_combo.pack(side="left", padx=4)
        self._combos.append((self.bg_mode_var, BG_OPTIONS, bg_combo))
        self.bg_swatch = tk.Canvas(row2, width=22, height=16, highlightthickness=1,
                                   highlightbackground="#999", background="#ffffff")
        self.bg_swatch.pack(side="left", padx=(8, 2))
        self.bg_label = self._make_label(row2, "背景:自动(白色)")
        self.bg_label.pack(side="left")
        self._make_button(row2, "取样背景色", self.sample_bg_hint).pack(side="left", padx=4)
        self._make_button(row2, "重置", self.reset_bg_color).pack(side="left")

        self.run_btn_stage1 = self._make_button(row2, "① 生成像素画", self.gen_stage1)
        self.run_btn_stage1.pack(side="left", padx=16)
        self.run_btn_stage2 = self._make_button(row2, "② 生成MC投影", self.gen_stage2)
        self.run_btn_stage2.pack(side="left")
        self.run_btn_all = self._make_button(row2, "一键生成全部", self.gen_all)
        self.run_btn_all.pack(side="left", padx=8)

        # ---- 行3：阶段2 参数 ----
        row3 = ttk.Frame(bar)
        row3.pack(fill="x", **pad)
        self._make_label(row3, "MC调色板:").pack(side="left")
        self.mc_palette_var = tk.StringVar(value=self._t(PALETTE_OPTIONS[0][1]))
        pal_combo = ttk.Combobox(row3, textvariable=self.mc_palette_var, state="readonly",
                                 values=self._spec_values(PALETTE_OPTIONS), width=18)
        pal_combo.pack(side="left", padx=4)
        self._combos.append((self.mc_palette_var, PALETTE_OPTIONS, pal_combo))
        self._make_label(row3, "抖动:").pack(side="left", padx=(10, 0))
        self.dither_var = tk.StringVar(value=self._t(DITHER_OPTIONS[0][1]))
        dith_combo = ttk.Combobox(row3, textvariable=self.dither_var, state="readonly",
                                  values=self._spec_values(DITHER_OPTIONS), width=18)
        dith_combo.pack(side="left", padx=4)
        self._combos.append((self.dither_var, DITHER_OPTIONS, dith_combo))
        self._make_label(row3, "颜色:").pack(side="left", padx=(10, 0))
        self.cs_var = tk.StringVar(value="lab")
        frm = ttk.Frame(row3)
        frm.pack(side="left")
        ttk.Radiobutton(frm, text="lab", variable=self.cs_var, value="lab").pack(side="left")
        ttk.Radiobutton(frm, text="rgb", variable=self.cs_var, value="rgb").pack(side="left", padx=(4, 0))
        self._make_label(row3, "放大scale:").pack(side="left", padx=(10, 0))
        self.scale_var = tk.IntVar(value=1)
        ttk.Spinbox(row3, from_=1, to=16, width=3, textvariable=self.scale_var).pack(side="left")
        self._make_label(row3, "厚度:").pack(side="left", padx=(10, 0))
        self.thick_var = tk.IntVar(value=1)
        ttk.Spinbox(row3, from_=1, to=16, width=3, textvariable=self.thick_var).pack(side="left")
        self._make_label(row3, "背面填充:").pack(side="left", padx=(10, 0))
        self.backing_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.backing_var, width=16).pack(side="left", padx=4)

        # ---- 行4：阶段2 原点/名称 + 导出 ----
        row4 = ttk.Frame(bar)
        row4.pack(fill="x", **pad)
        self._make_label(row4, "原点X Y Z:").pack(side="left")
        self.ox_var, self.oy_var, self.oz_var = (tk.StringVar(value="0"),
                                                 tk.StringVar(value="0"), tk.StringVar(value="0"))
        for v in (self.ox_var, self.oy_var, self.oz_var):
            ttk.Entry(row4, textvariable=v, width=5).pack(side="left", padx=2)
        self._make_label(row4, "名称:").pack(side="left", padx=(10, 0))
        self.name_var = tk.StringVar(value="像素画")
        ttk.Entry(row4, textvariable=self.name_var, width=14).pack(side="left", padx=4)
        self._make_label(row4, "作者:").pack(side="left", padx=(10, 0))
        self.author_var = tk.StringVar(value="")
        ttk.Entry(row4, textvariable=self.author_var, width=10).pack(side="left", padx=4)

        self._make_label(row4, "朝向:").pack(side="left", padx=(12, 0))
        self.orientation_var = tk.StringVar(value="wall")
        ofrm = ttk.Frame(row4)
        ofrm.pack(side="left")
        self._make_radio(ofrm, "竖放(墙面/平视)", self.orientation_var, "wall").pack(side="left")
        self._make_radio(ofrm, "横放(地面/俯视)", self.orientation_var, "floor").pack(side="left", padx=(4, 0))

        self._make_label(row4, "导出:").pack(side="left", padx=(16, 0))
        self._make_button(row4, "纯像素画PNG", self.export_pure).pack(side="left", padx=2)
        self._make_button(row4, "打开输出文件夹", self.open_outdir).pack(side="left", padx=2)

        # ---- 行5：预览选项 ----
        row5 = ttk.Frame(bar)
        row5.pack(fill="x", **pad)
        self.show_grid_var = tk.BooleanVar(value=False)
        self._make_check(row5, "显示网格", self.show_grid_var,
                         command=self.refresh_pixel_preview).pack(side="left")
        self._make_label(row5, "像素画格子:").pack(side="left", padx=(10, 0))
        self.cell_var = tk.IntVar(value=DEFAULT_CELL)
        ttk.Combobox(row5, textvariable=self.cell_var, state="readonly", width=4,
                     values=CELL_SIZES).pack(side="left", padx=4)
        self.cell_var.trace_add("write", lambda *_: self.refresh_pixel_preview())
        self._make_label(row5, "MC预览格子:").pack(side="left", padx=(14, 0))
        self.mc_cell_var = tk.IntVar(value=DEFAULT_MC_CELL)
        ttk.Combobox(row5, textvariable=self.mc_cell_var, state="readonly", width=4,
                     values=MC_CELL_SIZES).pack(side="left", padx=4)
        self.mc_cell_var.trace_add("write", lambda *_: self.refresh_mc_preview())

        # ---- 中部预览区 ----
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=2)
        self.pixel_frame, self.pixel_canvas = self._make_canvas(
            paned, "左：像素画（点击格子取样背景色）")
        paned.add(self.pixel_frame, weight=1)
        self.mc_frame, self.mc_canvas = self._make_canvas(paned, "右：Minecraft 方块预览")
        paned.add(self.mc_frame, weight=1)
        self.pixel_canvas.bind("<Button-1>", self.on_pixel_click)

        # ---- 底部：像素画信息 ----
        bottom = self._reg(ttk.LabelFrame(self.root, text=self._t("像素画信息")), "像素画信息")
        bottom.pack(fill="x", padx=8, pady=(2, 4))
        self.info_label = self._make_label(bottom, "尚未生成像素画", foreground="#888")
        self.info_label.pack(anchor="w", padx=6, pady=4)

        # ---- 进度 + 日志 ----
        prog = ttk.Frame(self.root)
        prog.pack(fill="x", padx=8)
        self.progress = ttk.Progressbar(prog, mode="determinate", maximum=100)
        self.progress.pack(fill="x", side="left", expand=True)
        self.progress_label = ttk.Label(prog, text="", width=34)
        self.progress_label.pack(side="left", padx=8)
        self.log = tk.Text(self.root, height=5, state="disabled", wrap="word")
        self.log.pack(fill="x", padx=8, pady=(2, 4))

        # ---- 状态栏 ----
        self.status = ttk.Label(self.root, text=self._t("请选择一张图片开始"), anchor="w",
                                relief="sunken", padding=(8, 3))
        self.status.pack(fill="x", side="bottom")

    def _make_canvas(self, parent, title):
        frame = ttk.Frame(parent)
        self._make_label(frame, title, foreground="#666").grid(
            row=0, column=0, columnspan=2, sticky="w")
        cv = tk.Canvas(frame, background="#ffffff", highlightthickness=1,
                       highlightbackground="#ccc")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=cv.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=cv.xview)
        cv.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        cv.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        return frame, cv

    # ------------------------------------------------------------- 事件
    def _on_size_change(self, _event=None):
        if self.size_var.get() in ("自定义", "Custom"):
            self.custom_frame.pack(side="left", padx=4, before=self.keep_aspect_check)
        else:
            self.custom_frame.pack_forget()

    def choose_image(self):
        path = filedialog.askopenfilename(
            title=self._t("选择图片"),
            filetypes=[(self._t("图片文件"), "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
                       (self._t("所有文件"), "*.*")])
        if not path:
            return
        try:
            img = pipeline.load_image_rgb(path)
        except Exception as exc:
            messagebox.showerror(self._t("打开失败"), self._tfmt(
                "无法打开图片：\n{exc}", "Could not open image:\n{exc}", exc=exc))
            return
        self.original_image = img
        self.image_path = path
        self.file_label.config(text=os.path.basename(path), foreground="#222")
        if not self.outdir_var.get().strip():
            self.outdir_var.set(os.path.dirname(os.path.abspath(path)))
        self.set_status(self._tfmt(
            "已加载图片 {w}×{h}，点击「① 生成像素画」",
            "Loaded {w}×{h} image. Click ① Generate Pixel Art.",
            w=img.width, h=img.height))
        self._log(self._tfmt(
            "已加载图片: {p} ({w}×{h})", "Loaded image: {p} ({w}×{h})",
            p=path, w=img.width, h=img.height))

    def pick_outdir(self):
        d = filedialog.askdirectory(title=self._t("选择输出文件夹"))
        if d:
            self.outdir_var.set(d)

    def open_outdir(self):
        d = self.last_out_dir or self.outdir_var.get().strip()
        if d and os.path.isdir(d):
            if sys.platform == "win32":
                os.startfile(d)  # noqa
            else:
                import subprocess
                subprocess.Popen(["xdg-open", d])

    # ------------------------------------------------- 尺寸与参数收集
    def _current_size(self):
        sel = self.size_var.get()
        if sel in ("自定义", "Custom"):
            try:
                w = max(1, min(MAX_DIM, int(self.custom_w.get())))
                h = max(1, min(MAX_DIM, int(self.custom_h.get())))
            except (tk.TclError, ValueError):
                messagebox.showwarning(self._t("提示"), self._t(
                    "自定义宽高需为 1~4096 的整数"))
                return None
            return w, h
        w, h = sel.split("×")
        return int(w), int(h)

    def _stage1_kwargs(self):
        size = self._current_size()
        if size is None:
            return None
        w, h = size
        background = self._combo_id(BG_OPTIONS, self.bg_mode_var)
        return dict(
            width=w, height=h,
            background=background,
            bg_color=self.bg_color,
            preserve_aspect=self.keep_aspect_var.get(),
        )

    def _stage2_kwargs(self):
        try:
            scale = max(1, int(self.scale_var.get()))
            thickness = max(1, int(self.thick_var.get()))
            origin = (int(self.ox_var.get()), int(self.oy_var.get()), int(self.oz_var.get()))
        except (tk.TclError, ValueError):
            messagebox.showerror(self._t("错误"), self._t("放大倍数/厚度/原点必须是整数"))
            return None
        out_dir = self.outdir_var.get().strip()
        if not out_dir:
            out_dir = os.path.dirname(os.path.abspath(self.image_path))
        stem = os.path.splitext(os.path.basename(self.image_path))[0]
        return dict(
            mc_palette=self._combo_id(PALETTE_OPTIONS, self.mc_palette_var),
            dither=self._combo_id(DITHER_OPTIONS, self.dither_var),
            color_space=self.cs_var.get(),
            scale=scale, thickness=thickness,
            backing=self.backing_var.get().strip() or None,
            origin=origin,
            name=self.name_var.get().strip() or "像素画",
            author=self.author_var.get().strip(),
            orientation=self.orientation_var.get(),
            out_path=os.path.join(out_dir, stem + ".litematic"),
        )

    # -------------------------------------------------------- 后台工作
    def _busy(self, flag):
        self.run_btn_stage1.configure(state="disabled" if flag else "normal")
        self.run_btn_stage2.configure(state="disabled" if flag else "normal")
        self.run_btn_all.configure(state="disabled" if flag else "normal")

    def _push_progress(self, pct, stage):
        self.q.put(("PROGRESS", pct, stage))

    def gen_stage1(self):
        if self.original_image is None:
            messagebox.showinfo(self._t("提示"), self._t("请先选择一张图片"))
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo(self._t("提示"), self._t("正在处理中，请稍候…"))
            return
        kw = self._stage1_kwargs()
        if kw is None:
            return
        self._start_worker(self._work_stage1, kw, self._t("生成像素画"))

    def gen_stage2(self):
        if self.stage1 is None:
            messagebox.showinfo(self._t("提示"), self._t("请先点击「① 生成像素画」"))
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo(self._t("提示"), self._t("正在处理中，请稍候…"))
            return
        kw = self._stage2_kwargs()
        if kw is None:
            return
        self._start_worker(self._work_stage2, kw, self._t("生成MC投影"))

    def gen_all(self):
        if self.original_image is None:
            messagebox.showinfo(self._t("提示"), self._t("请先选择一张图片"))
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo(self._t("提示"), self._t("正在处理中，请稍候…"))
            return
        kw1 = self._stage1_kwargs()
        kw2 = self._stage2_kwargs()
        if kw1 is None or kw2 is None:
            return
        self._start_worker(self._work_all, (kw1, kw2), self._t("一键生成"))

    def _start_worker(self, fn, arg, label):
        self._busy(True)
        self.progress.configure(value=0)
        self.progress_label.configure(text=self._t("准备中…"))
        self._log(self._tfmt("开始{label}…", "Starting {label}…", label=label))
        self.worker = threading.Thread(target=fn, args=(arg,), daemon=True)
        self.worker.start()

    def _work_stage1(self, kw):
        try:
            res = pipeline.run_stage1(self.original_image, progress_cb=self._push_progress, **kw)
            self.q.put(("STAGE1", res))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", self._tfmt(
                "生成像素画失败: {e}", "Failed to generate pixel art: {e}", e=e)))

    def _work_stage2(self, kw):
        try:
            res = pipeline.run_stage2(self.stage1, progress_cb=self._push_progress, **kw)
            self.q.put(("STAGE2", res))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", self._tfmt(
                "生成MC投影失败: {e}", "Failed to generate MC projection: {e}", e=e)))

    def _work_all(self, pair):
        kw1, kw2 = pair
        try:
            res1 = pipeline.run_stage1(self.original_image, progress_cb=self._push_progress, **kw1)
            self.q.put(("STAGE1", res1))
            res2 = pipeline.run_stage2(res1, progress_cb=self._push_progress, **kw2)
            self.q.put(("STAGE2", res2))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", self._tfmt(
                "转换失败: {e}", "Conversion failed: {e}", e=e)))

    def _poll_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0]
                if kind == "PROGRESS":
                    _, pct, stage = item
                    self.progress.configure(value=pct)
                    self.progress_label.configure(text=self._tfmt(
                        "{stage}… {pct:.0f}%", "{stage}… {pct:.0f}%", stage=stage, pct=pct))
                elif kind == "STAGE1":
                    self._on_stage1(item[1])
                elif kind == "STAGE2":
                    self._on_stage2(item[1])
                elif kind == "ERROR":
                    self._busy(False)
                    self.progress_label.configure(text=self._t("失败"))
                    self._log(f"❌ {item[1]}")
                    messagebox.showerror(self._t("错误"), item[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------ 结果
    def _on_stage1(self, res):
        self.stage1 = res
        gw, gh = res.size
        if res.background == "glass":
            bg_note = (self._tfmt("，识别背景 {n} 格（将填玻璃）",
                                  ", bg detected: {n} cells (will be glass)", n=res.removed)
                       if res.trimmed else self._t("，未检测到背景"))
        elif res.background == "trim":
            bg_note = (self._tfmt("，去除背景 {n} 格", ", bg removed: {n} cells", n=res.removed)
                       if res.trimmed else self._t("，未检测到背景"))
        else:
            bg_note = ""
        self.info_label.config(text=self._tfmt(
            "像素画尺寸 {w}×{h} 格（每格=1像素）{note}",
            "Pixel art {w}×{h} cells (1px = 1 cell){note}",
            w=gw, h=gh, note=bg_note))
        self.refresh_pixel_preview()
        self._busy(False)
        self.progress.configure(value=48)
        self.progress_label.configure(text=self._t("阶段1完成"))
        self.set_status(self._tfmt("像素画生成完成：{w}×{h}{note}",
                                   "Pixel art ready: {w}×{h}{note}",
                                   w=gw, h=gh, note=bg_note))
        self._log(self._tfmt("✅ 阶段1 像素画: {w}×{h} 格{note}",
                             "✅ Stage 1 pixel art: {w}×{h} cells{note}",
                             w=gw, h=gh, note=bg_note))

    def _on_stage2(self, res):
        self.stage2 = res
        self.last_out_dir = os.path.dirname(res["out"])
        self.refresh_mc_preview()
        self._busy(False)
        self.progress.configure(value=100)
        self.progress_label.configure(text=self._t("完成"))
        self.set_status(self._tfmt("MC投影生成完成：{summary}", "MC projection ready: {summary}",
                                   summary=pipeline.block_usage_summary(res)))
        self._log(self._tfmt("✅ 阶段2 {summary}", "✅ Stage 2 {summary}",
                             summary=pipeline.block_usage_summary(res)))
        self._log(self._tfmt("   投影: {p} ({kb} KB)", "   Projection: {p} ({kb} KB)",
                             p=res["out"], kb=res["file_size"] / 1024))
        if res.get("preview"):
            self._log(self._tfmt("   预览: {p}", "   Preview: {p}", p=res["preview"]))
        if res.get("stats"):
            self._log(self._tfmt("   统计: {p}", "   Stats: {p}", p=res["stats"]))
        if res.get("glass_fixed") and res["glass_fixed"] != (0, 0):
            rem, add = res["glass_fixed"]
            self._log(self._tfmt("   玻璃去噪: 移除孤立玻璃 {r} 格，填补玻璃空洞 {a} 格",
                                 "   Glass cleanup: removed {r}, filled {a}", r=rem, a=add))
        if res.get("bg_glass_cells"):
            self._log(self._tfmt("   背景填玻璃: {n} 格", "   Background glass: {n} cells",
                                 n=res["bg_glass_cells"]))
        messagebox.showinfo(self._t("完成"), self._tfmt(
            "MC投影已生成：\n{out}", "MC projection generated:\n{out}", out=res["out"]))

    # ------------------------------------------------------------ 预览
    def refresh_pixel_preview(self):
        if self.stage1 is None:
            return
        grid = self.stage1.grid
        gh, gw = len(grid), len(grid[0])
        cell = self.cell_var.get()
        if gw * cell > MAX_PREVIEW_PX or gh * cell > MAX_PREVIEW_PX:
            cell = 1
        img = pipeline.render_grid_preview(grid, cell=cell,
                                           show_grid=self.show_grid_var.get())
        self._show_on_canvas(self.pixel_canvas, img)

    def refresh_mc_preview(self):
        if self.stage2 is None:
            return
        grid = self.stage2["block_grid"]
        w, h = self.stage2["w"], self.stage2["h"]
        img = pixelart2litematic.render_preview(grid, (w, h), cell=self.mc_cell_var.get())
        self._show_on_canvas(self.mc_canvas, img)

    def _show_on_canvas(self, cv, img):
        cv.delete("all")
        photo = ImageTk.PhotoImage(img)
        self._photo_refs.append(photo)
        cv.create_image(0, 0, image=photo, anchor="nw")
        cv.configure(scrollregion=(0, 0, img.width, img.height))

    # -------------------------------------------------------- 背景取样
    def _bg_mode_active(self):
        return self._combo_id(BG_OPTIONS, self.bg_mode_var) in ("trim", "glass")

    def sample_bg_hint(self):
        if self.stage1 is None:
            messagebox.showinfo(
                self._t("提示"),
                self._t("请先点击「① 生成像素画」，然后点击左侧图纸中的背景格子取样背景色"))
        else:
            self.set_status(self._t(
                "请点击左侧像素画中的【背景格子】取样背景色（背景处理选「去除背景」或「背景填玻璃」后生效）"))

    def on_pixel_click(self, event):
        if self.stage1 is None:
            self.set_status(self._t("请先生成像素画，再点击图纸取样背景色"))
            return
        grid = self.stage1.grid
        cell = self.cell_var.get()
        gh, gw = len(grid), len(grid[0])
        if gw * cell > MAX_PREVIEW_PX or gh * cell > MAX_PREVIEW_PX:
            cell = 1
        x, y = event.x // cell, event.y // cell
        if not (0 <= y < gh and 0 <= x < gw):
            return
        color = grid[y][x]
        if color is None:
            self.set_status(self._t("该位置为空白，请点击实心格子取样背景色"))
            return
        self.bg_color = tuple(color)
        self._update_bg_ui()
        if self._bg_mode_active():
            self.gen_stage1()
            self.set_status(self._tfmt("已取样背景色 {c}，已重新生成",
                                       "Bg color sampled: {c}, regenerated",
                                       c=self._hex(color)))
        else:
            self.set_status(self._tfmt(
                "已取样背景色 {c}（背景处理选「去除背景」或「背景填玻璃」后生效）",
                "Bg color sampled: {c} (works with Remove / Glass background)",
                c=self._hex(color)))

    def reset_bg_color(self):
        self.bg_color = None
        self._update_bg_ui()
        if self._bg_mode_active() and self.stage1 is not None:
            self.gen_stage1()
            self.set_status(self._t("背景色已重置为自动(白色)，已重新生成"))
        else:
            self.set_status(self._t("背景色已重置为自动(白色)"))

    @staticmethod
    def _hex(rgb):
        return "#%02X%02X%02X" % tuple(rgb)

    def _update_bg_ui(self):
        if self.bg_color is None:
            self.bg_swatch.configure(background="#ffffff")
            self.bg_label.config(text=self._t("背景:自动(白色)"))
        else:
            hex_str = self._hex(self.bg_color)
            self.bg_swatch.configure(background=hex_str)
            self.bg_label.config(text=self._tfmt("背景:{hex}", "Background: {hex}", hex=hex_str))

    # ------------------------------------------------------------ 导出
    def export_pure(self):
        if self.stage1 is None:
            messagebox.showinfo(self._t("提示"), self._t("请先点击「① 生成像素画」"))
            return
        path = filedialog.asksaveasfilename(
            title=self._t("导出纯像素画 PNG（每格=1px）"), defaultextension=".png",
            initialfile=f"像素画_{self.stage1.size[0]}x{self.stage1.size[1]}.png",
            filetypes=[(self._t("PNG 图片"), "*.png")])
        if not path:
            return
        try:
            self.stage1.pure_image.save(path)
        except Exception as exc:
            messagebox.showerror(self._t("导出失败"), self._tfmt(
                "导出失败：\n{exc}", "Export failed:\n{exc}", exc=exc))
            return
        self.set_status(self._tfmt(
            "纯像素画已导出（{w}×{h} 像素，每像素=1 格）：{p}",
            "Pixel art exported ({w}×{h}, 1px = 1 cell): {p}",
            w=self.stage1.pure_image.width, h=self.stage1.pure_image.height, p=path))
        messagebox.showinfo(self._t("导出成功"), self._tfmt(
            "纯像素画已保存到：\n{path}", "Pixel art saved to:\n{path}", path=path))

    # ------------------------------------------------------------ 其他
    def set_status(self, text):
        self.status.config(text=text)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


# ---------------------------------------------------------------------------
# 无界面自检：验证打包环境完整可用（与语言无关）
# ---------------------------------------------------------------------------
def self_test():
    import traceback
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(sys.executable)), "self_test_output")
    os.makedirs(out_dir, exist_ok=True)
    try:
        from PIL import ImageDraw as _ID
        img = Image.new("RGB", (120, 90))
        px = img.load()
        for y in range(90):
            for x in range(120):
                px[x, y] = (int(255 * x / 120), int(160 * y / 90), 120)
        d = _ID.Draw(img)
        d.ellipse([20, 15, 75, 70], fill=(235, 90, 70))
        d.rectangle([85, 10, 115, 35], fill=(30, 120, 210))
        src = os.path.join(out_dir, "selftest_input.png")
        img.save(src)

        # 完整两阶段管道
        res = pipeline.run_pipeline(
            src, width=64, height=64, mc_palette="auto", dither="floyd",
            color_space="lab", scale=1, thickness=1, out_dir=out_dir,
            export_pixel_art=True)
        s1, s2 = res["stage1"], res["stage2"]
        assert s2["w"] == 64 and s2["h"] == 64, (s2["w"], s2["h"])
        assert os.path.exists(s2["out"]) and s2["file_size"] > 0
        assert s2["total_blocks"] > 0

        # 去除背景 + 保持宽高比 + 3D 厚度
        bordered = Image.new("RGB", (160, 120), (255, 255, 255))
        inner = Image.new("RGB", (80, 80), (255, 255, 255))
        i_px = inner.load()
        for y in range(80):
            for x in range(80):
                if (x - 40) ** 2 + (y - 40) ** 2 <= 40 ** 2:
                    i_px[x, y] = (235, 90, 70)
        bordered.paste(inner, (40, 20))
        src2 = os.path.join(out_dir, "selftest_trim.png")
        bordered.save(src2)
        res2 = pipeline.run_pipeline(
            src2, width=64, height=64, preserve_aspect=True,
            background="trim", mc_palette="concrete", dither="none",
            color_space="rgb", thickness=2, backing="minecraft:white_concrete",
            out_dir=out_dir)
        s1b, s2b = res2["stage1"], res2["stage2"]
        assert s1b.trimmed and s1b.removed > 0, (s1b.removed, s1b.size)
        assert s2b["thickness"] == 2
        assert s2b["total_blocks"] > 0

        msg = (f"SELF TEST OK\n"
               f"case1: {s1.size[0]}x{s1.size[1]} 格 → {s2['total_blocks']} 方块 "
               f"({s2['distinct_blocks']} 种), {os.path.basename(s2['out'])} "
               f"({s2['file_size']/1024:.1f} KB)\n"
               f"case2: trim removed={s1b.removed} 格, size={s1b.size}, "
               f"thickness={s2b['thickness']}, blocks={s2b['total_blocks']}\n"
               f"out={out_dir}")
    except Exception:
        msg = "SELF TEST FAILED\n" + traceback.format_exc()
    with open(os.path.join(out_dir, "self_test_result.txt"), "w", encoding="utf-8") as f:
        f.write(msg)
    try:
        print(msg)
    except Exception:
        pass


def main():
    dpi_aware()
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        try:
            main()
        except Exception:
            import traceback
            tb = traceback.format_exc()
            log_dir = os.path.dirname(os.path.abspath(
                sys.executable if getattr(sys, "frozen", False) else __file__))
            try:
                log_path = os.path.join(log_dir, "图片转MC像素画投影_error.log")
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(tb)
                messagebox.showerror("程序启动失败", f"发生错误，详情已写入：\n{log_path}\n\n{tb}")
            except Exception:
                messagebox.showerror("程序启动失败", tb)
