# -*- coding: utf-8 -*-
"""GUI 冒烟测试：无人工点击，走一遍界面核心路径
（加载图片 → 阶段1 → 预览 → 阶段2 → 预览），验证界面代码可用。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from PIL import Image, ImageDraw

import main as gui

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
os.makedirs(WORK, exist_ok=True)


def make_test_image(path):
    img = Image.new("RGB", (80, 60))
    d = ImageDraw.Draw(img)
    for y in range(60):
        for x in range(80):
            d.point((x, y), fill=(int(255 * x / 80), int(160 * y / 60), 120))
    d.ellipse([15, 10, 60, 50], fill=(235, 90, 70))
    img.save(path)
    return path


def pump(app):
    """把队列中的消息处理完（等价于 mainloop 里的一次轮询）。"""
    app._poll_queue()


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")
        except Exception:
            pass
    # 屏蔽弹窗，避免阻塞
    gui.messagebox.showinfo = lambda *a, **k: None
    gui.messagebox.showerror = lambda *a, **k: None

    src = make_test_image(os.path.join(WORK, "gui_input.png"))
    root = tk.Tk()
    root.withdraw()
    app = gui.App(root)
    root.update()

    # 1) 加载图片（跳过文件对话框）
    app.image_path = src
    app.original_image = gui.pipeline.load_image_rgb(src)
    app.outdir_var.set(WORK)
    app.file_label.config(text=os.path.basename(src))
    root.update()

    # 2) 阶段1
    kw1 = app._stage1_kwargs()
    assert kw1 is not None and kw1["width"] == 48 and kw1["height"] == 48
    app._work_stage1(kw1)          # 同步执行
    pump(app)
    assert app.stage1 is not None, "阶段1 应产出结果"
    assert app.stage1.size == (48, 48), app.stage1.size
    assert len(app._photo_refs) > 0, "像素画预览应已渲染"
    print(f"  ✅ 阶段1 GUI 路径: {app.stage1.size} 格")

    # 3) 取样背景色（模拟点击预览：直接调用回调逻辑）
    color = app.stage1.grid[app.stage1.size[1] // 2][0]
    if color is not None:
        app.bg_color = tuple(color)
        app._update_bg_ui()
        assert app.bg_label.cget("text").startswith("背景:"), app.bg_label.cget("text")
    print(f"  ✅ 背景色取样 UI: {app.bg_label.cget('text')}")

    # 4) 阶段2
    kw2 = app._stage2_kwargs()
    assert kw2 is not None
    app._work_stage2(kw2)          # 同步执行
    pump(app)
    assert app.stage2 is not None, "阶段2 应产出结果"
    assert os.path.exists(app.stage2["out"]), app.stage2["out"]
    assert app.stage2["total_blocks"] > 0
    print(f"  ✅ 阶段2 GUI 路径: {app.stage2['w']}x{app.stage2['h']} → "
          f"{app.stage2['total_blocks']} 方块, 输出 {os.path.basename(app.stage2['out'])}")

    # 5) 一键生成（重新走一遍全流程）
    app._work_all((kw1, kw2))
    pump(app)
    assert app.stage1 is not None and app.stage2 is not None
    print("  ✅ 一键生成路径通过")

    root.destroy()
    print("\n🎉 GUI 冒烟测试通过")


if __name__ == "__main__":
    main()
