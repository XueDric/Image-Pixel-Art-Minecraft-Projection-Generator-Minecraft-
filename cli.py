# -*- coding: utf-8 -*-
"""命令行入口：图片 → 像素画 → Minecraft 投影 (.litematic)

用法示例:
    python cli.py 我的照片.png                          # 默认 48×48
    python cli.py 我的照片.png --size 64                 # 64×64
    python cli.py 我的照片.png --size 128 --keep-aspect  # 128 长边、保持宽高比
    python cli.py 我的照片.png --size 96 --mc-palette concrete --dither none
    python cli.py 我的照片.png --size 64 --trim          # 去除白色背景
    python cli.py 我的照片.png --size 64 --scale 2 --thickness 2 --backing white_concrete
    python cli.py 我的照片.png --size 128 --export-pixel-art  # 同时导出 1px 纯像素画PNG
    python cli.py 图1.png 图2.png 图3.png                # 批量转换

输出（默认与图片同目录）:
    {图片名}.litematic          MC 建筑投影（放 .minecraft/schematics 后游戏内加载）
    {图片名}.preview.png        方块化预览图
    {图片名}.stats.xlsx         方块材料清单（中文名/数量/色块，Excel）
"""
from __future__ import annotations

import argparse
import os
import sys

import pipeline

MC_PALETTE_HELP = "MC 方块调色板: " + " / ".join(pipeline.MC_PALETTE_VALUES)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="图片转MC像素画投影",
        description="把图片先转为像素画，再转为 Minecraft Litematica 建筑投影 (.litematic)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("images", nargs="*", help="输入图片路径（可多个，批量转换）")

    # ---- 阶段1：像素画 ----
    g1 = parser.add_argument_group("阶段1：像素画（保留原色）")
    g1.add_argument("--size", type=int, default=48,
                    help="像素画尺寸（正方形边长；与 --width/--height 同时使用时被覆盖）")
    g1.add_argument("--width", type=int, default=None, help="像素画宽度（自定义）")
    g1.add_argument("--height", type=int, default=None, help="像素画高度（自定义）")
    g1.add_argument("--keep-aspect", action="store_true",
                    help="保持原图宽高比（较长边 = 目标尺寸），不拉伸")
    g1.add_argument("--background", choices=["none", "trim", "glass"], default="none",
                    help="背景处理: none=不处理(默认) / trim=去除背景(镂空) / "
                         "glass=背景填玻璃（白色/取样色背景→玻璃，主体保持实体）")
    g1.add_argument("--trim", action="store_true",
                    help="等价于 --background trim（去除主体外背景，镂空）")
    g1.add_argument("--bg-glass", action="store_true",
                    help="等价于 --background glass（背景填玻璃）")
    g1.add_argument("--bg-color", default=None, metavar="RRGGBB",
                    help="去除/填玻璃时指定背景色（如 0188D3），默认自动白色")
    g1.add_argument("--export-pixel-art", action="store_true",
                    help="同时导出 1px/格 纯像素画 PNG")

    # ---- 阶段2：MC 投影 ----
    g2 = parser.add_argument_group("阶段2：Minecraft 投影")
    g2.add_argument("--mc-palette", default="auto", help=MC_PALETTE_HELP)
    g2.add_argument("--dither", choices=["none", "floyd"], default="floyd",
                    help="颜色抖动: none=最近色, floyd=Floyd–Steinberg 抖动")
    g2.add_argument("--color-space", choices=["lab", "rgb"], default="lab",
                    help="颜色距离: lab=感知距离(推荐), rgb=字面最近色")
    g2.add_argument("--scale", type=int, default=1, help="每个像素放大为 N×N 个方块")
    g2.add_argument("--thickness", type=int, default=1, help="方块厚度(z 方向层数)")
    g2.add_argument("--backing", default=None,
                    help="厚度>1 时的背面填充方块（默认用前景方块填满）")
    g2.add_argument("--origin", type=int, nargs=3, default=[0, 0, 0],
                    metavar=("X", "Y", "Z"), help="投影放置原点(左下角世界坐标)")
    g2.add_argument("--name", default="像素画", help="投影名称")
    g2.add_argument("--author", default="", help="作者")
    g2.add_argument("--description", default="", help="描述")
    g2.add_argument("--mc-data-version", type=int, default=3955,
                    help="Minecraft 数据版本号（1.21.1=3955, 1.21.4=4085）")
    g2.add_argument("--orientation", choices=["wall", "floor"], default="wall",
                    help="投影朝向: wall=竖放(墙面/平视, 图像在X-Y平面, 默认), "
                         "floor=横放(地面/俯视, 图像在X-Z平面)")
    g2.add_argument("--no-glass-cleanup", action="store_true",
                    help="关闭玻璃一致性去噪（默认消除孤立玻璃/实体噪点）")
    g2.add_argument("--no-preview", action="store_true", help="不生成方块化预览图")
    g2.add_argument("--no-stats", action="store_true", help="不生成方块用量统计 CSV")

    # ---- 输出 ----
    g3 = parser.add_argument_group("输出")
    g3.add_argument("-o", "--out-dir", default=None, help="输出目录（默认与图片同目录）")
    g3.add_argument("--cell", type=int, default=14, help="预览图每方块像素大小")
    g3.add_argument("--pause", action="store_true",
                    help="结束后停留等待按键（双击/拖放 exe 时自动生效）")
    g3.add_argument("--no-pause", action="store_true", help="结束后不等待按键")
    return parser


def should_pause(args, no_args=False):
    if args.no_pause:
        return False
    if args.pause:
        return True
    if sys.platform == "win32" and not sys.stdin.isatty():
        return True
    return False


def wait_exit(args, code):
    if should_pause(args):
        try:
            input("\n按回车键退出…")
        except EOFError:
            pass
    return code


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")
        except Exception:
            pass
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.images:
        parser.print_help()
        print("\n用法示例: python cli.py 我的照片.png --size 64")
        return wait_exit(args, 2)

    if args.width is not None or args.height is not None:
        width = args.width or args.size
        height = args.height or args.size
    else:
        width = height = args.size
    if not (1 <= width <= pipeline.MAX_DIM and 1 <= height <= pipeline.MAX_DIM):
        print(f"错误: 尺寸必须在 1~{pipeline.MAX_DIM} 之间")
        return wait_exit(args, 1)
    if args.scale < 1 or args.thickness < 1:
        print("错误: --scale / --thickness 必须 >= 1")
        return wait_exit(args, 1)

    bg_color = None
    if args.bg_color:
        try:
            hx = args.bg_color.lstrip("#")
            bg_color = tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            print(f"错误: 背景色格式应为 RRGGBB，如 0188D3（收到: {args.bg_color}）")
            return wait_exit(args, 1)

    background = args.background
    if args.trim and args.bg_glass:
        print("错误: --trim 与 --bg-glass 不能同时使用")
        return wait_exit(args, 1)
    if args.trim:
        background = "trim"
    if args.bg_glass:
        background = "glass"

    ok = 0
    for img_path in args.images:
        if not os.path.exists(img_path):
            print(f"错误: 找不到图片 {img_path}")
            continue
        try:
            result = pipeline.run_pipeline(
                img_path,
                width=width, height=height, preserve_aspect=args.keep_aspect,
                background=background, bg_color=bg_color,
                mc_palette=args.mc_palette, dither=args.dither,
                color_space=args.color_space, scale=args.scale,
                thickness=args.thickness, backing=args.backing,
                origin=tuple(args.origin), name=args.name, author=args.author,
                description=args.description,
                mc_data_version=args.mc_data_version,
                out_dir=args.out_dir,
                mc_preview=not args.no_preview, mc_stats=not args.no_stats,
                cell=args.cell,
                orientation=args.orientation,
                glass_cleanup=not args.no_glass_cleanup,
                export_pixel_art=args.export_pixel_art,
            )
        except Exception as e:  # noqa: BLE001
            print(f"错误: 转换 {img_path} 失败: {e}")
            continue
        ok += 1

        s1, s2 = result["stage1"], result["stage2"]
        gw, gh = s1.size
        if s1.background == "glass":
            bg_note = f"，识别背景 {s1.removed} 格（将填玻璃）" if s1.trimmed else "，未检测到背景"
        elif s1.background == "trim":
            bg_note = f"，去除背景 {s1.removed} 格" if s1.trimmed else "，未检测到背景"
        else:
            bg_note = ""
        print(f"\n[完成] {os.path.basename(img_path)}")
        print(f"  阶段1 像素画: {gw}×{gh} 格{bg_note}")
        print(f"  阶段2 MC投影: {pipeline.block_usage_summary(s2)}")
        print(f"    投影: {s2['out']} ({s2['file_size'] / 1024:.1f} KB)")
        if s2["preview"]:
            print(f"    预览: {s2['preview']}")
        if s2["stats"]:
            print(f"    统计: {s2['stats']}")
        if result["pixel_art_path"]:
            print(f"    像素画: {result['pixel_art_path']}")
        if s2.get("glass_fixed") and s2["glass_fixed"] != (0, 0):
            rem, add = s2["glass_fixed"]
            print(f"    玻璃去噪: 移除孤立玻璃 {rem} 格，填补玻璃空洞 {add} 格")
        if s2.get("bg_glass_cells"):
            print(f"    背景填玻璃: {s2['bg_glass_cells']} 格")

    print("\n使用方法: 把 .litematic 放入 .minecraft/schematics 文件夹，")
    print("在游戏中用 Litematica 加载投影（投影→加载原理图），配合 litematica-printer 可自动建造。")
    return wait_exit(args, 0 if ok else 1)


if __name__ == "__main__":
    sys.exit(main())
