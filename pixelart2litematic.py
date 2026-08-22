# -*- coding: utf-8 -*-
"""像素画 → Minecraft 方块 → Litematica 建筑投影 (.litematic) 转换工具。

命令行用法示例:
    python pixelart2litematic.py 我的像素画.png
    python pixelart2litematic.py 图1.png 图2.png              # 批量转换
    python pixelart2litematic.py 我的像素画.png --scale 2 --palette concrete --dither floyd
    python pixelart2litematic.py 我的像素画.png --thickness 2 --backing minecraft:white_concrete
    python pixelart2litematic.py 我的像素画.png --color-space rgb   # 字面最近色(红色→红色羊毛)

输出:
    - .litematic 投影文件（放进 .minecraft/schematics 后可在 Litematica 中加载投影，
      配合 litematica-printer 可自动建造）
    - 预览图 PNG
    - 方块用量统计 CSV（方便准备材料）
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

from PIL import Image, ImageDraw

from mc_palette import ColorMatcher, get_palette, palette_info, ALL_BLOCKS
from litematic_writer import BlockState, RegionBuilder, Schematic

BLOCK_COLOR = {bid: rgb for bid, rgb in ALL_BLOCKS.items()}

DITHER_WEIGHTS = [  # (dx, dy, weight) Floyd–Steinberg
    (1, 0, 7 / 16),
    (-1, 1, 3 / 16),
    (0, 1, 5 / 16),
    (1, 1, 1 / 16),
]


def parse_block_ref(ref: str):
    """解析 'minecraft:white_concrete' 或 'white_concrete' 或 'white_concrete[prop=v]'"""
    ref = ref.strip()
    if ref.lower() == "air":
        return BlockState("minecraft:air")
    props = {}
    if "[" in ref:
        ref, propstr = ref[:-1].split("[", 1)
        for part in propstr.split(","):
            k, _, v = part.partition("=")
            props[k.strip()] = v.strip()
    if not ref.startswith("minecraft:"):
        ref = "minecraft:" + ref
    return BlockState(ref, props)


def load_pixels(path: str):
    """读取图像为 RGBA 模式。"""
    return Image.open(path).convert("RGBA")


def match_image(img, matcher, dither="none", transparent_threshold=128, progress_cb=None):
    """逐像素匹配方块，返回 (H, W) 的 (block_id, rgb) 网格。

    :param dither: 'none' 或 'floyd'（Floyd–Steinberg 抖动）
    :param progress_cb: 可选回调 progress_cb(pct: float, stage: str)
    """
    w, h = img.size
    rgba = img.load()
    buf = [[list(rgba[x, y]) for x in range(w)] for y in range(h)]
    grid = [[None] * w for _ in range(h)]

    def report(pct, stage="匹配颜色"):
        if progress_cb:
            progress_cb(pct, stage)

    if matcher.vectorized and dither == "none":
        # ---- 快速路径：numpy 整图批量匹配（无抖动）----
        np = matcher._np
        arr = np.asarray(buf, dtype=np.float64)  # (H, W, 4)
        alpha = arr[..., 3]
        valid = alpha >= transparent_threshold
        rgb_flat = arr[..., :3].reshape(-1, 3)[valid.reshape(-1)]
        ids, matched_rgb = matcher.match_batch(rgb_flat)
        it = iter(ids)
        irgb = iter(matched_rgb)
        vf = valid.reshape(-1)
        for i in range(h * w):
            if vf[i]:
                bid = next(it)
                brgb = next(irgb)
                grid[i // w][i % w] = (bid, (int(brgb[0]), int(brgb[1]), int(brgb[2])))
            else:
                grid[i // w][i % w] = ("minecraft:air", (0, 0, 0))
        report(90.0)
        return grid, (w, h)

    # ---- 常规路径：逐像素（含抖动）----
    total = h * w
    last_pct = -1
    for y in range(h):
        for x in range(w):
            r, g, b, a = buf[y][x]
            if a < transparent_threshold:
                grid[y][x] = ("minecraft:air", (0, 0, 0))
            else:
                r = min(255, max(0, r))
                g = min(255, max(0, g))
                b = min(255, max(0, b))
                block_id, block_rgb = matcher.match((r, g, b))
                grid[y][x] = (block_id, block_rgb)
                if dither == "floyd":
                    err = (r - block_rgb[0], g - block_rgb[1], b - block_rgb[2])
                    for dx, dy, wt in DITHER_WEIGHTS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and buf[ny][nx][3] >= transparent_threshold:
                            c = buf[ny][nx]
                            c[0] += err[0] * wt
                            c[1] += err[1] * wt
                            c[2] += err[2] * wt
            pct = (y * w + x + 1) / total * 90.0
            if progress_cb and int(pct) != last_pct:
                last_pct = int(pct)
                progress_cb(pct, "匹配颜色")
    report(90.0)
    return grid, (w, h)


def build_schematic(grid, size, origin, scale, thickness, backing, name, author, description,
                    mc_data_version, progress_cb=None, orientation="wall"):
    """把匹配好的方块网格转成 Schematic。

    :param progress_cb: 可选回调 progress_cb(done_rows, total_rows)，用于大图进度提示。
    :param orientation: 'wall'=竖放（墙面/平视，图像在 X-Y 平面，厚度沿 +Z 向外，默认）；
                        'floor'=横放（地面/俯视，图像在 X-Z 平面，厚度沿 +Y 向上）。
                        两种朝向图像第 0 行（顶部）都放在"远离观察者"的一侧：
                        wall → 最高 y；floor → 最大 z（站在 +Z 侧向北看为正）。
    """
    w, h = size
    ox, oy, oz = origin
    floor = orientation == "floor"
    W = w * scale
    if floor:
        H = thickness
        L = h * scale
    else:
        H = h * scale
        L = thickness
    region = RegionBuilder("像素画", origin=(ox, oy, oz), size=(W, H, L))

    backing_state = parse_block_ref(backing) if backing else None

    counts = {}
    for py in range(h):
        row = grid[py]
        for px in range(w):
            block_id, _ = row[px]
            if block_id == "minecraft:air":
                continue
            state = BlockState(block_id)
            if floor:
                # 图像第 0 行（顶部）→ 最大 z（站在 +Z 侧俯视时图像为正立）
                for dx in range(scale):
                    for dy in range(scale):
                        bx = ox + px * scale + dx
                        bz = oz + (h - 1 - py) * scale + dy
                        region.set_block(bx, oy, bz, state)
                        counts[block_id] = counts.get(block_id, 0) + 1
                        if thickness > 1:
                            fill = backing_state if backing_state is not None else state
                            for dy2 in range(1, thickness):
                                region.set_block(bx, oy + dy2, bz, fill)
                                counts[fill.name] = counts.get(fill.name, 0) + 1
            else:
                # 图像第 0 行（顶部）→ 最高 y；图像底部 → 最低 y
                for dx in range(scale):
                    for dy in range(scale):
                        bx = ox + px * scale + dx
                        by = oy + (h - 1 - py) * scale + dy
                        region.set_block(bx, by, oz, state)
                        counts[block_id] = counts.get(block_id, 0) + 1
                        if thickness > 1:
                            fill = backing_state if backing_state is not None else state
                            for dz in range(1, thickness):
                                region.set_block(bx, by, oz + dz, fill)
                                counts[fill.name] = counts.get(fill.name, 0) + 1
        if progress_cb is not None:
            progress_cb(py + 1, h)

    sch = Schematic(name=name, author=author, description=description,
                    mc_data_version=mc_data_version)
    sch.add_region(region)
    return sch, counts


def render_preview(grid, size, cell=14, out_path=None):
    """把方块网格渲染成带轻微立体感的预览图（numpy 向量化，PIL 兜底）。

    预览图单边超过 4096 像素时自动缩小 cell，避免超大图内存/耗时爆炸。
    """
    w, h = size
    max_side = 4096
    if w * cell > max_side or h * cell > max_side:
        cell = max(1, min(cell, max_side // max(w, h)))
    try:
        import numpy as np
        colors = np.zeros((h, w, 3), dtype=np.float64)
        for y in range(h):
            for x in range(w):
                block_id, rgb = grid[y][x]
                if block_id != "minecraft:air":
                    colors[y, x] = rgb
        base = np.repeat(np.repeat(colors, cell, axis=0), cell, axis=1)  # (H*cell, W*cell, 3)
        edge = max(1, cell // 4)
        row_idx = np.arange(h * cell) % cell
        col_idx = np.arange(w * cell) % cell
        top_mask = (row_idx < edge)[:, None] & np.ones((1, w * cell), dtype=bool)
        left_mask = np.ones((h * cell, 1), dtype=bool) & (col_idx < edge)[None, :]
        bottom_mask = (row_idx >= cell - edge)[:, None] & np.ones((1, w * cell), dtype=bool)
        right_mask = np.ones((h * cell, 1), dtype=bool) & (col_idx >= cell - edge)[None, :]
        # 空气区域保持透明
        base = np.concatenate([base, np.full((h * cell, w * cell, 1), 0.0)], axis=2)
        air = (base[..., :3].sum(axis=2) == 0)
        base[..., 3] = np.where(air, 0.0, 255.0)
        base[top_mask, 0:3] = np.minimum(255.0, base[top_mask, 0:3] * 1.18)
        base[left_mask, 0:3] = np.minimum(255.0, base[left_mask, 0:3] * 1.18)
        base[bottom_mask, 0:3] = base[bottom_mask, 0:3] * 0.72
        base[right_mask, 0:3] = base[right_mask, 0:3] * 0.72
        base[..., 3] = np.where(air, 0.0, base[..., 3])
        img = Image.fromarray(base.astype(np.uint8), "RGBA")
        if out_path:
            img.save(out_path)
        return img
    except ImportError:
        img = Image.new("RGBA", (w * cell, h * cell), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            for x in range(w):
                block_id, rgb = grid[y][x]
                if block_id == "minecraft:air":
                    continue
                x0, y0 = x * cell, y * cell
                base = rgb
                top = tuple(min(255, int(c * 1.18)) for c in base)
                shadow = tuple(int(c * 0.72) for c in base)
                draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=base + (255,))
                edge = max(1, cell // 4)
                draw.rectangle([x0, y0, x0 + cell - 1, y0 + edge - 1], fill=top + (255,))
                draw.rectangle([x0, y0, x0 + edge - 1, y0 + cell - 1], fill=top + (255,))
                draw.rectangle([x0, y0 + cell - edge, x0 + cell - 1, y0 + cell - 1], fill=shadow + (255,))
                draw.rectangle([x0 + cell - edge, y0, x0 + cell - 1, y0 + cell - 1], fill=shadow + (255,))
        if out_path:
            img.save(out_path)
        return img


def write_stats(path, counts):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["方块", "数量", "颜色(RGB)"])
        for bid, cnt in sorted(counts.items(), key=lambda kv: -kv[1]):
            rgb = BLOCK_COLOR.get(bid, (0, 0, 0))
            writer.writerow([bid, cnt, "#%02X%02X%02X" % rgb])
    return sum(counts.values())


def convert_image(image_path, out=None, scale=1, palette="auto", dither="floyd",
                  color_space="lab", thickness=1, backing=None, origin=(0, 0, 0),
                  name="像素画", author="", description="", mc_data_version=3955,
                  preview=True, stats=True, cell=14, flip_x=False, flip_y=False,
                  progress_cb=None):
    """核心转换函数：图片 → .litematic (+ 预览图 + 统计 CSV)。

    :param progress_cb: 可选回调 progress_cb(pct: float 0-100, stage: str)
    返回结果字典: {out, preview, stats, w, h, total_blocks, distinct_blocks, ...}
    """
    def report(pct, stage):
        if progress_cb:
            progress_cb(pct, stage)

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"找不到图片: {image_path}")
    if scale < 1:
        raise ValueError("scale 必须 >= 1")
    if thickness < 1:
        raise ValueError("thickness 必须 >= 1")

    report(1.0, "读取图片")
    stem = os.path.splitext(os.path.basename(image_path))[0]
    base_dir = os.path.dirname(os.path.abspath(image_path))
    out = out or os.path.join(base_dir, stem + ".litematic")
    preview_path = None
    stats_path = None
    if preview:
        preview_path = stem + ".preview.png"
        if not os.path.isabs(preview_path):
            preview_path = os.path.join(base_dir, preview_path)
    if stats:
        stats_path = stem + ".stats.csv"
        if not os.path.isabs(stats_path):
            stats_path = os.path.join(base_dir, stats_path)

    img = load_pixels(image_path)
    if flip_x:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if flip_y:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    matcher = ColorMatcher(get_palette(palette), color_space)
    grid, (w, h) = match_image(img, matcher, dither=dither, progress_cb=progress_cb)

    report(91.0, "生成投影")
    sch, counts = build_schematic(
        grid, (w, h), tuple(origin), scale, thickness, backing,
        name, author, description, mc_data_version,
    )
    raw_size = sch.save(out)
    total_blocks = sum(counts.values())

    if preview:
        report(96.0, "渲染预览")
        render_preview(grid, (w, h), cell=cell, out_path=preview_path)
    if stats:
        write_stats(stats_path, counts)
    report(100.0, "完成")

    return {
        "out": out,
        "preview": preview_path,
        "stats": stats_path,
        "w": w, "h": h,
        "total_blocks": total_blocks,
        "distinct_blocks": len(counts),
        "raw_size": raw_size,
        "file_size": os.path.getsize(out),
    }


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pixelart2litematic",
        description="把像素画图片转换为 Minecraft Litematica 建筑投影 (.litematic)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("images", nargs="*", help="输入图片路径（可多个，批量转换）")
    parser.add_argument("-o", "--out", help="输出 .litematic 路径（批量时无效，默认与图片同名）")
    parser.add_argument("--scale", type=int, default=1, help="每个像素放大为 N×N 个方块")
    parser.add_argument("--palette", default="auto",
                        help="方块调色板: auto/wool/concrete/terracotta/glass/"
                             "wool+concrete/concrete+terracotta/misc")
    parser.add_argument("--dither", choices=["none", "floyd"], default="floyd",
                        help="颜色抖动: none=最近色, floyd=Floyd–Steinberg 抖动")
    parser.add_argument("--color-space", choices=["lab", "rgb"], default="lab",
                        help="颜色距离计算空间: lab=感知距离(推荐), rgb=字面最近色(红色→红色羊毛)")
    parser.add_argument("--thickness", type=int, default=1, help="方块厚度(z 方向层数)")
    parser.add_argument("--backing", default=None,
                        help="厚度>1 时的背面填充方块（默认用前景方块填满）")
    parser.add_argument("--origin", type=int, nargs=3, default=[0, 0, 0],
                        metavar=("X", "Y", "Z"), help="投影放置原点(左下角世界坐标)")
    parser.add_argument("--name", default="像素画", help="投影名称")
    parser.add_argument("--author", default="", help="作者")
    parser.add_argument("--description", default="", help="描述")
    parser.add_argument("--mc-data-version", type=int, default=3955,
                        help="Minecraft 数据版本号（1.21.1=3955, 1.21.4=4085）")
    parser.add_argument("--preview", default=None, help="预览图输出路径（默认 <输出>.preview.png）")
    parser.add_argument("--no-preview", action="store_true", help="不生成预览图")
    parser.add_argument("--stats", default=None, help="方块用量统计 CSV 路径（默认 <输出>.stats.csv）")
    parser.add_argument("--no-stats", action="store_true", help="不生成统计 CSV")
    parser.add_argument("--cell", type=int, default=14, help="预览图每方块像素大小")
    parser.add_argument("--flip-x", action="store_true", help="水平翻转图像")
    parser.add_argument("--flip-y", action="store_true", help="垂直翻转图像")
    parser.add_argument("--pause", action="store_true",
                        help="结束后停留等待按键（双击/拖放 exe 时自动生效）")
    parser.add_argument("--no-pause", action="store_true", help="结束后不等待按键")
    return parser


def should_pause(args, no_args=False):
    """双击/拖放到 exe 时（无终端）自动停留，方便查看结果。"""
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
    # Windows 控制台默认 GBK，先兜底避免 emoji 等字符导致 UnicodeEncodeError
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
        print("\n用法示例: python pixelart2litematic.py 我的像素画.png --scale 2")
        return wait_exit(args, 2)

    if args.scale < 1:
        print("错误: --scale 必须 >= 1")
        return wait_exit(args, 1)
    if args.thickness < 1:
        print("错误: --thickness 必须 >= 1")
        return wait_exit(args, 1)

    ok = 0
    for img_path in args.images:
        if not os.path.exists(img_path):
            print(f"错误: 找不到图片 {img_path}")
            continue
        try:
            result = convert_image(
                img_path,
                out=args.out if len(args.images) == 1 else None,
                scale=args.scale,
                palette=args.palette,
                dither=args.dither,
                color_space=args.color_space,
                thickness=args.thickness,
                backing=args.backing,
                origin=tuple(args.origin),
                name=args.name,
                author=args.author,
                description=args.description,
                mc_data_version=args.mc_data_version,
                preview=not args.no_preview,
                stats=not args.no_stats,
                cell=args.cell,
                flip_x=args.flip_x,
                flip_y=args.flip_y,
            )
        except Exception as e:
            print(f"错误: 转换 {img_path} 失败: {e}")
            continue
        ok += 1
        print(f"[完成] {os.path.basename(img_path)}: {result['w']}x{result['h']} 像素 "
              f"→ {result['w']*args.scale}x{result['h']*args.scale}x{args.thickness} 方块，"
              f"共 {result['total_blocks']} 个方块 / {result['distinct_blocks']} 种")
        print(f"   投影: {result['out']} ({result['file_size']/1024:.1f} KB)")
        if result["preview"]:
            print(f"   预览: {result['preview']}")
        if result["stats"]:
            print(f"   统计: {result['stats']}")

    print("\n使用方法: 把 .litematic 放入 .minecraft/schematics 文件夹，")
    print("在游戏中用 Litematica 加载投影（投影→加载原理图），配合 litematica-printer 可自动建造。")
    return wait_exit(args, 0 if ok else 1)


if __name__ == "__main__":
    sys.exit(main())
