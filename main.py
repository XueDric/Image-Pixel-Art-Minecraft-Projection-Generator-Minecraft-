# -*- coding: utf-8 -*-
"""
main.py —— 图片 → 像素画 → Minecraft 投影 生成器（图形界面）

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

APP_TITLE = "图片 → 像素画 → Minecraft投影 生成器"

# 阶段1
SIZE_PRESETS = pipeline.SIZE_PRESETS
MAX_DIM = pipeline.MAX_DIM
CELL_SIZES = [1, 2, 4, 8, 10, 12, 16, 20, 24, 32]
DEFAULT_CELL = 16
MAX_PREVIEW_PX = 4096

# 阶段2
MC_PALETTE_KINDS = pipeline.MC_PALETTE_KINDS
MC_PALETTE_VALUES = pipeline.MC_PALETTE_VALUES
DITHER_KINDS = pipeline.DITHER_KINDS
DITHER_VALUES = pipeline.DITHER_VALUES
MC_CELL_SIZES = [4, 8, 12, 14, 16, 20, 24, 32]
DEFAULT_MC_CELL = 14


def dpi_aware():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
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

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        pad = {"padx": 6, "pady": 3}

        bar = ttk.LabelFrame(self.root, text="控制面板")
        bar.pack(fill="x", padx=8, pady=6)

        # ---- 行0：图片 / 输出目录 ----
        row0 = ttk.Frame(bar)
        row0.pack(fill="x", **pad)
        ttk.Button(row0, text="① 选择图片...", command=self.choose_image).pack(side="left")
        self.file_label = ttk.Label(row0, text="未选择图片", foreground="#888")
        self.file_label.pack(side="left", padx=8)
        ttk.Label(row0, text="输出目录:").pack(side="left", padx=(16, 0))
        self.outdir_var = tk.StringVar()
        ttk.Entry(row0, textvariable=self.outdir_var, width=28).pack(side="left", padx=4)
        ttk.Button(row0, text="选择…", command=self.pick_outdir).pack(side="left")

        # ---- 行1：阶段1 尺寸 ----
        row1 = ttk.Frame(bar)
        row1.pack(fill="x", **pad)
        ttk.Label(row1, text="阶段1 像素尺寸:").pack(side="left")
        self.size_var = tk.StringVar(value=SIZE_PRESETS[3])   # 默认 48×48
        self.size_combo = ttk.Combobox(row1, textvariable=self.size_var,
                                       values=SIZE_PRESETS, state="readonly", width=8)
        self.size_combo.pack(side="left", padx=4)
        self.size_combo.bind("<<ComboboxSelected>>", self._on_size_change)

        self.custom_w = tk.IntVar(value=64)
        self.custom_h = tk.IntVar(value=48)
        self.custom_frame = ttk.Frame(row1)
        self.custom_frame.pack(side="left", padx=4)
        ttk.Label(self.custom_frame, text="宽:").pack(side="left")
        ttk.Spinbox(self.custom_frame, from_=1, to=MAX_DIM, width=4,
                    textvariable=self.custom_w).pack(side="left")
        ttk.Label(self.custom_frame, text="高:").pack(side="left", padx=(6, 0))
        ttk.Spinbox(self.custom_frame, from_=1, to=MAX_DIM, width=4,
                    textvariable=self.custom_h).pack(side="left")
        self.custom_frame.pack_forget()

        self.keep_aspect_var = tk.BooleanVar(value=False)
        self.keep_aspect_check = ttk.Checkbutton(row1, text="保持宽高比",
                                                 variable=self.keep_aspect_var)
        self.keep_aspect_check.pack(side="left", padx=8)

        # ---- 行2：阶段1 背景处理 / 生成按钮 ----
        row2 = ttk.Frame(bar)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="背景处理:").pack(side="left")
        self.bg_mode_var = tk.StringVar(value="无")
        self.bg_mode_combo = ttk.Combobox(row2, textvariable=self.bg_mode_var,
                                          state="readonly", width=16,
                                          values=["无", "去除背景(镂空)", "背景填玻璃"])
        self.bg_mode_combo.pack(side="left", padx=4)
        self.bg_swatch = tk.Canvas(row2, width=22, height=16, highlightthickness=1,
                                   highlightbackground="#999", background="#ffffff")
        self.bg_swatch.pack(side="left", padx=(8, 2))
        self.bg_label = ttk.Label(row2, text="背景:自动(白色)")
        self.bg_label.pack(side="left")
        ttk.Button(row2, text="取样背景色", command=self.sample_bg_hint).pack(side="left", padx=4)
        ttk.Button(row2, text="重置", command=self.reset_bg_color).pack(side="left")

        self.run_btn_stage1 = ttk.Button(row2, text="① 生成像素画", command=self.gen_stage1)
        self.run_btn_stage1.pack(side="left", padx=16)
        self.run_btn_stage2 = ttk.Button(row2, text="② 生成MC投影", command=self.gen_stage2)
        self.run_btn_stage2.pack(side="left")
        self.run_btn_all = ttk.Button(row2, text="一键生成全部", command=self.gen_all)
        self.run_btn_all.pack(side="left", padx=8)

        # ---- 行3：阶段2 参数 ----
        row3 = ttk.Frame(bar)
        row3.pack(fill="x", **pad)
        ttk.Label(row3, text="MC调色板:").pack(side="left")
        self.mc_palette_var = tk.StringVar(value=MC_PALETTE_KINDS[0])
        ttk.Combobox(row3, textvariable=self.mc_palette_var, state="readonly",
                     values=MC_PALETTE_KINDS, width=18).pack(side="left", padx=4)
        ttk.Label(row3, text="抖动:").pack(side="left", padx=(10, 0))
        self.dither_var = tk.StringVar(value=DITHER_KINDS[0])
        ttk.Combobox(row3, textvariable=self.dither_var, state="readonly",
                     values=DITHER_KINDS, width=18).pack(side="left", padx=4)
        ttk.Label(row3, text="颜色:").pack(side="left", padx=(10, 0))
        self.cs_var = tk.StringVar(value="lab")
        frm = ttk.Frame(row3)
        frm.pack(side="left")
        ttk.Radiobutton(frm, text="lab", variable=self.cs_var, value="lab").pack(side="left")
        ttk.Radiobutton(frm, text="rgb", variable=self.cs_var, value="rgb").pack(side="left", padx=(4, 0))
        ttk.Label(row3, text="放大scale:").pack(side="left", padx=(10, 0))
        self.scale_var = tk.IntVar(value=1)
        ttk.Spinbox(row3, from_=1, to=16, width=3, textvariable=self.scale_var).pack(side="left")
        ttk.Label(row3, text="厚度:").pack(side="left", padx=(10, 0))
        self.thick_var = tk.IntVar(value=1)
        ttk.Spinbox(row3, from_=1, to=16, width=3, textvariable=self.thick_var).pack(side="left")
        ttk.Label(row3, text="背面填充:").pack(side="left", padx=(10, 0))
        self.backing_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.backing_var, width=16).pack(side="left", padx=4)

        # ---- 行4：阶段2 原点/名称 + 导出 ----
        row4 = ttk.Frame(bar)
        row4.pack(fill="x", **pad)
        ttk.Label(row4, text="原点X Y Z:").pack(side="left")
        self.ox_var, self.oy_var, self.oz_var = (tk.StringVar(value="0"),
                                                 tk.StringVar(value="0"), tk.StringVar(value="0"))
        for v in (self.ox_var, self.oy_var, self.oz_var):
            ttk.Entry(row4, textvariable=v, width=5).pack(side="left", padx=2)
        ttk.Label(row4, text="名称:").pack(side="left", padx=(10, 0))
        self.name_var = tk.StringVar(value="像素画")
        ttk.Entry(row4, textvariable=self.name_var, width=14).pack(side="left", padx=4)
        ttk.Label(row4, text="作者:").pack(side="left", padx=(10, 0))
        self.author_var = tk.StringVar(value="")
        ttk.Entry(row4, textvariable=self.author_var, width=10).pack(side="left", padx=4)

        ttk.Label(row4, text="朝向:").pack(side="left", padx=(12, 0))
        self.orientation_var = tk.StringVar(value="wall")
        ofrm = ttk.Frame(row4)
        ofrm.pack(side="left")
        ttk.Radiobutton(ofrm, text="竖放(墙面/平视)", variable=self.orientation_var,
                        value="wall").pack(side="left")
        ttk.Radiobutton(ofrm, text="横放(地面/俯视)", variable=self.orientation_var,
                        value="floor").pack(side="left", padx=(4, 0))

        ttk.Label(row4, text="导出:").pack(side="left", padx=(16, 0))
        ttk.Button(row4, text="纯像素画PNG", command=self.export_pure).pack(side="left", padx=2)
        ttk.Button(row4, text="打开输出文件夹", command=self.open_outdir).pack(side="left", padx=2)

        # ---- 行5：预览选项 ----
        row5 = ttk.Frame(bar)
        row5.pack(fill="x", **pad)
        self.show_grid_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row5, text="显示网格", variable=self.show_grid_var,
                        command=self.refresh_pixel_preview).pack(side="left")
        ttk.Label(row5, text="像素画格子:").pack(side="left", padx=(10, 0))
        self.cell_var = tk.IntVar(value=DEFAULT_CELL)
        ttk.Combobox(row5, textvariable=self.cell_var, state="readonly", width=4,
                     values=CELL_SIZES).pack(side="left", padx=4)
        self.cell_var.trace_add("write", lambda *_: self.refresh_pixel_preview())
        ttk.Label(row5, text="MC预览格子:").pack(side="left", padx=(14, 0))
        self.mc_cell_var = tk.IntVar(value=DEFAULT_MC_CELL)
        ttk.Combobox(row5, textvariable=self.mc_cell_var, state="readonly", width=4,
                     values=MC_CELL_SIZES).pack(side="left", padx=4)
        self.mc_cell_var.trace_add("write", lambda *_: self.refresh_mc_preview())

        # ---- 中部预览区 ----
        paned = ttk.PanedWindow(self.root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=2)
        self.pixel_frame, self.pixel_canvas = self._make_canvas(paned, "左：像素画（点击格子取样背景色）")
        paned.add(self.pixel_frame, weight=1)
        self.mc_frame, self.mc_canvas = self._make_canvas(paned, "右：Minecraft 方块预览")
        paned.add(self.mc_frame, weight=1)
        self.pixel_canvas.bind("<Button-1>", self.on_pixel_click)

        # ---- 底部：像素画信息 ----
        bottom = ttk.LabelFrame(self.root, text="像素画信息")
        bottom.pack(fill="x", padx=8, pady=(2, 4))
        self.info_label = ttk.Label(bottom, text="尚未生成像素画", foreground="#888")
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
        self.status = ttk.Label(self.root, text="请选择一张图片开始", anchor="w",
                                relief="sunken", padding=(8, 3))
        self.status.pack(fill="x", side="bottom")

    def _make_canvas(self, parent, title):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text=title, foreground="#666").grid(
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
        if self.size_var.get() == "自定义":
            self.custom_frame.pack(side="left", padx=4, before=self.keep_aspect_check)
        else:
            self.custom_frame.pack_forget()

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
                       ("所有文件", "*.*")])
        if not path:
            return
        try:
            img = pipeline.load_image_rgb(path)
        except Exception as exc:
            messagebox.showerror("打开失败", f"无法打开图片：\n{exc}")
            return
        self.original_image = img
        self.image_path = path
        self.file_label.config(text=os.path.basename(path), foreground="#222")
        if not self.outdir_var.get().strip():
            self.outdir_var.set(os.path.dirname(os.path.abspath(path)))
        self.set_status(f"已加载图片 {img.width}×{img.height}，点击「① 生成像素画」")
        self._log(f"已加载图片: {path} ({img.width}×{img.height})")

    def pick_outdir(self):
        d = filedialog.askdirectory(title="选择输出文件夹")
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
        if sel == "自定义":
            try:
                w = max(1, min(MAX_DIM, int(self.custom_w.get())))
                h = max(1, min(MAX_DIM, int(self.custom_h.get())))
            except (tk.TclError, ValueError):
                messagebox.showwarning("提示", "自定义宽高需为 1~4096 的整数")
                return None
            return w, h
        w, h = sel.split("×")
        return int(w), int(h)

    def _stage1_kwargs(self):
        size = self._current_size()
        if size is None:
            return None
        w, h = size
        mode = self.bg_mode_var.get()
        background = {"无": "none", "去除背景(镂空)": "trim", "背景填玻璃": "glass"}[mode]
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
            messagebox.showerror("错误", "放大倍数/厚度/原点必须是整数")
            return None
        out_dir = self.outdir_var.get().strip()
        if not out_dir:
            out_dir = os.path.dirname(os.path.abspath(self.image_path))
        stem = os.path.splitext(os.path.basename(self.image_path))[0]
        return dict(
            mc_palette=MC_PALETTE_VALUES[MC_PALETTE_KINDS.index(self.mc_palette_var.get())],
            dither=DITHER_VALUES[DITHER_KINDS.index(self.dither_var.get())],
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
            messagebox.showinfo("提示", "请先选择一张图片")
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("提示", "正在处理中，请稍候…")
            return
        kw = self._stage1_kwargs()
        if kw is None:
            return
        self._start_worker(self._work_stage1, kw, "生成像素画")

    def gen_stage2(self):
        if self.stage1 is None:
            messagebox.showinfo("提示", "请先点击「① 生成像素画」")
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("提示", "正在处理中，请稍候…")
            return
        kw = self._stage2_kwargs()
        if kw is None:
            return
        self._start_worker(self._work_stage2, kw, "生成MC投影")

    def gen_all(self):
        if self.original_image is None:
            messagebox.showinfo("提示", "请先选择一张图片")
            return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("提示", "正在处理中，请稍候…")
            return
        kw1 = self._stage1_kwargs()
        kw2 = self._stage2_kwargs()
        if kw1 is None or kw2 is None:
            return
        self._start_worker(self._work_all, (kw1, kw2), "一键生成")

    def _start_worker(self, fn, arg, label):
        self._busy(True)
        self.progress.configure(value=0)
        self.progress_label.configure(text="准备中…")
        self._log(f"开始{label}…")
        self.worker = threading.Thread(target=fn, args=(arg,), daemon=True)
        self.worker.start()

    def _work_stage1(self, kw):
        try:
            res = pipeline.run_stage1(self.original_image, progress_cb=self._push_progress, **kw)
            self.q.put(("STAGE1", res))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", f"生成像素画失败: {e}"))

    def _work_stage2(self, kw):
        try:
            res = pipeline.run_stage2(self.stage1, progress_cb=self._push_progress, **kw)
            self.q.put(("STAGE2", res))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", f"生成MC投影失败: {e}"))

    def _work_all(self, pair):
        kw1, kw2 = pair
        try:
            res1 = pipeline.run_stage1(self.original_image, progress_cb=self._push_progress, **kw1)
            self.q.put(("STAGE1", res1))
            res2 = pipeline.run_stage2(res1, progress_cb=self._push_progress, **kw2)
            self.q.put(("STAGE2", res2))
        except Exception as e:  # noqa: BLE001
            self.q.put(("ERROR", f"转换失败: {e}"))

    def _poll_queue(self):
        try:
            while True:
                item = self.q.get_nowait()
                kind = item[0]
                if kind == "PROGRESS":
                    _, pct, stage = item
                    self.progress.configure(value=pct)
                    self.progress_label.configure(text=f"{stage}… {pct:.0f}%")
                elif kind == "STAGE1":
                    self._on_stage1(item[1])
                elif kind == "STAGE2":
                    self._on_stage2(item[1])
                elif kind == "ERROR":
                    self._busy(False)
                    self.progress_label.configure(text="失败")
                    self._log(f"❌ {item[1]}")
                    messagebox.showerror("错误", item[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    # ------------------------------------------------------------ 结果
    def _on_stage1(self, res):
        self.stage1 = res
        gw, gh = res.size
        if res.background == "glass":
            bg_note = f"，识别背景 {res.removed} 格（将填玻璃）" if res.trimmed else "，未检测到背景"
        elif res.background == "trim":
            bg_note = f"，去除背景 {res.removed} 格" if res.trimmed else "，未检测到背景"
        else:
            bg_note = ""
        self.info_label.config(text=f"像素画尺寸 {gw}×{gh} 格（每格=1像素）{bg_note}")
        self.refresh_pixel_preview()
        self._busy(False)
        self.progress.configure(value=48)
        self.progress_label.configure(text="阶段1完成")
        self.set_status(f"像素画生成完成：{gw}×{gh}{bg_note}")
        self._log(f"✅ 阶段1 像素画: {gw}×{gh} 格{bg_note}")

    def _on_stage2(self, res):
        self.stage2 = res
        self.last_out_dir = os.path.dirname(res["out"])
        self.refresh_mc_preview()
        self._busy(False)
        self.progress.configure(value=100)
        self.progress_label.configure(text="完成")
        self.set_status(f"MC投影生成完成：{pipeline.block_usage_summary(res)}")
        self._log(f"✅ 阶段2 {pipeline.block_usage_summary(res)}")
        self._log(f"   投影: {res['out']} ({res['file_size']/1024:.1f} KB)")
        if res.get("preview"):
            self._log(f"   预览: {res['preview']}")
        if res.get("stats"):
            self._log(f"   统计: {res['stats']}")
        if res.get("glass_fixed") and res["glass_fixed"] != (0, 0):
            rem, add = res["glass_fixed"]
            self._log(f"   玻璃去噪: 移除孤立玻璃 {rem} 格，填补玻璃空洞 {add} 格")
        if res.get("bg_glass_cells"):
            self._log(f"   背景填玻璃: {res['bg_glass_cells']} 格")
        messagebox.showinfo("完成", f"MC投影已生成：\n{res['out']}")

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
        return self.bg_mode_var.get() in ("去除背景(镂空)", "背景填玻璃")

    def sample_bg_hint(self):
        if self.stage1 is None:
            messagebox.showinfo("提示", "请先点击「① 生成像素画」，然后点击左侧图纸中的背景格子取样背景色")
        else:
            self.set_status("请点击左侧像素画中的【背景格子】取样背景色（背景处理选「去除背景」或「背景填玻璃」后生效）")

    def on_pixel_click(self, event):
        if self.stage1 is None:
            self.set_status("请先生成像素画，再点击图纸取样背景色")
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
            self.set_status("该位置为空白，请点击实心格子取样背景色")
            return
        self.bg_color = tuple(color)
        self._update_bg_ui()
        if self._bg_mode_active():
            self.gen_stage1()
            self.set_status(f"已取样背景色 {self._hex(color)}，已重新生成")
        else:
            self.set_status(f"已取样背景色 {self._hex(color)}（背景处理选「去除背景」或「背景填玻璃」后生效）")

    def reset_bg_color(self):
        self.bg_color = None
        self._update_bg_ui()
        if self._bg_mode_active() and self.stage1 is not None:
            self.gen_stage1()
            self.set_status("背景色已重置为自动(白色)，已重新生成")
        else:
            self.set_status("背景色已重置为自动(白色)")

    @staticmethod
    def _hex(rgb):
        return "#%02X%02X%02X" % tuple(rgb)

    def _update_bg_ui(self):
        if self.bg_color is None:
            self.bg_swatch.configure(background="#ffffff")
            self.bg_label.config(text="背景:自动(白色)")
        else:
            hex_str = self._hex(self.bg_color)
            self.bg_swatch.configure(background=hex_str)
            self.bg_label.config(text=f"背景:{hex_str}")

    # ------------------------------------------------------------ 导出
    def export_pure(self):
        if self.stage1 is None:
            messagebox.showinfo("提示", "请先点击「① 生成像素画」")
            return
        path = filedialog.asksaveasfilename(
            title="导出纯像素画 PNG（每格=1px）", defaultextension=".png",
            initialfile=f"像素画_{self.stage1.size[0]}x{self.stage1.size[1]}.png",
            filetypes=[("PNG 图片", "*.png")])
        if not path:
            return
        try:
            self.stage1.pure_image.save(path)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return
        self.set_status(f"纯像素画已导出（{self.stage1.pure_image.width}×{self.stage1.pure_image.height} 像素，每像素=1 格）：{path}")
        messagebox.showinfo("导出成功", f"纯像素画已保存到：\n{path}")

    # ------------------------------------------------------------ 其他
    def set_status(self, text):
        self.status.config(text=text)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


# ---------------------------------------------------------------------------
# 无界面自检：验证打包环境完整可用
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
