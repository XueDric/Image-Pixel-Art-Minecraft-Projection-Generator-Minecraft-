# -*- coding: utf-8 -*-
"""Minecraft 方块颜色调色板。

每个条目: (方块 ID, (R, G, B))。颜色取自 Minecraft 官方方块颜色/常见工具约定值，
用于把像素画颜色匹配到最近的 MC 方块。
"""
from __future__ import annotations

# ---------- 16 色羊毛 ----------
WOOL = {
    "minecraft:white_wool": (233, 236, 236),
    "minecraft:orange_wool": (240, 118, 19),
    "minecraft:magenta_wool": (189, 68, 179),
    "minecraft:light_blue_wool": (58, 175, 217),
    "minecraft:yellow_wool": (248, 198, 39),
    "minecraft:lime_wool": (112, 185, 25),
    "minecraft:pink_wool": (237, 141, 172),
    "minecraft:gray_wool": (62, 68, 71),
    "minecraft:light_gray_wool": (156, 161, 161),
    "minecraft:cyan_wool": (21, 137, 145),
    "minecraft:purple_wool": (100, 32, 156),
    "minecraft:blue_wool": (53, 69, 151),
    "minecraft:brown_wool": (112, 68, 30),
    "minecraft:green_wool": (88, 107, 24),
    "minecraft:red_wool": (160, 39, 34),
    "minecraft:black_wool": (25, 22, 25),
}

# ---------- 16 色混凝土 ----------
CONCRETE = {
    "minecraft:white_concrete": (207, 207, 207),
    "minecraft:orange_concrete": (224, 100, 3),
    "minecraft:magenta_concrete": (164, 48, 159),
    "minecraft:light_blue_concrete": (36, 137, 199),
    "minecraft:yellow_concrete": (240, 181, 14),
    "minecraft:lime_concrete": (109, 160, 60),
    "minecraft:pink_concrete": (217, 130, 161),
    "minecraft:gray_concrete": (55, 58, 62),
    "minecraft:light_gray_concrete": (140, 140, 140),
    "minecraft:cyan_concrete": (21, 137, 145),
    "minecraft:purple_concrete": (100, 32, 156),
    "minecraft:blue_concrete": (51, 51, 162),
    "minecraft:brown_concrete": (107, 62, 27),
    "minecraft:green_concrete": (76, 90, 31),
    "minecraft:red_concrete": (142, 33, 33),
    "minecraft:black_concrete": (8, 10, 15),
}

# ---------- 16 色陶瓦 ----------
TERRACOTTA = {
    "minecraft:white_terracotta": (209, 177, 161),
    "minecraft:orange_terracotta": (219, 124, 61),
    "minecraft:magenta_terracotta": (169, 92, 133),
    "minecraft:light_blue_terracotta": (107, 140, 168),
    "minecraft:yellow_terracotta": (216, 176, 79),
    "minecraft:lime_terracotta": (123, 141, 85),
    "minecraft:pink_terracotta": (168, 120, 107),
    "minecraft:gray_terracotta": (88, 75, 67),
    "minecraft:light_gray_terracotta": (139, 129, 118),
    "minecraft:cyan_terracotta": (108, 123, 130),
    "minecraft:purple_terracotta": (121, 99, 107),
    "minecraft:blue_terracotta": (74, 75, 96),
    "minecraft:brown_terracotta": (119, 89, 78),
    "minecraft:green_terracotta": (89, 99, 75),
    "minecraft:red_terracotta": (153, 84, 62),
    "minecraft:black_terracotta": (43, 39, 38),
}

# ---------- 16 色染色玻璃 ----------
GLASS = {
    "minecraft:white_stained_glass": (255, 255, 255),
    "minecraft:orange_stained_glass": (242, 128, 14),
    "minecraft:magenta_stained_glass": (195, 84, 214),
    "minecraft:light_blue_stained_glass": (78, 183, 232),
    "minecraft:yellow_stained_glass": (249, 223, 46),
    "minecraft:lime_stained_glass": (108, 235, 59),
    "minecraft:pink_stained_glass": (245, 161, 190),
    "minecraft:gray_stained_glass": (76, 76, 76),
    "minecraft:light_gray_stained_glass": (174, 174, 174),
    "minecraft:cyan_stained_glass": (42, 166, 166),
    "minecraft:purple_stained_glass": (163, 43, 212),
    "minecraft:blue_stained_glass": (58, 67, 207),
    "minecraft:brown_stained_glass": (122, 74, 27),
    "minecraft:green_stained_glass": (74, 122, 27),
    "minecraft:red_stained_glass": (176, 46, 38),
    "minecraft:black_stained_glass": (29, 29, 29),
}

# ---------- 常用装饰/建材方块 ----------
MISC = {
    "minecraft:quartz_block": (236, 229, 216),
    "minecraft:smooth_quartz": (236, 229, 216),
    "minecraft:snow_block": (249, 255, 255),
    "minecraft:bone_block": (233, 230, 213),
    "minecraft:calcite": (221, 231, 228),
    "minecraft:white_glazed_terracotta": (209, 199, 166),
    "minecraft:gold_block": (253, 245, 95),
    "minecraft:iron_block": (219, 219, 219),
    "minecraft:diamond_block": (74, 237, 217),
    "minecraft:emerald_block": (23, 221, 98),
    "minecraft:lapis_block": (25, 71, 209),
    "minecraft:redstone_block": (176, 43, 38),
    "minecraft:coal_block": (20, 21, 25),
    "minecraft:netherite_block": (60, 60, 60),
    "minecraft:copper_block": (201, 118, 91),
    "minecraft:exposed_copper": (150, 132, 108),
    "minecraft:weathered_copper": (100, 143, 128),
    "minecraft:oxidized_copper": (72, 141, 132),
    "minecraft:amethyst_block": (154, 92, 198),
    "minecraft:stone": (127, 127, 127),
    "minecraft:cobblestone": (125, 125, 125),
    "minecraft:mossy_cobblestone": (105, 121, 105),
    "minecraft:stone_bricks": (126, 126, 126),
    "minecraft:cracked_stone_bricks": (121, 121, 121),
    "minecraft:mossy_stone_bricks": (102, 118, 102),
    "minecraft:chiseled_stone_bricks": (126, 126, 126),
    "minecraft:bricks": (153, 95, 61),
    "minecraft:deepslate": (72, 72, 72),
    "minecraft:cobbled_deepslate": (70, 70, 70),
    "minecraft:deepslate_bricks": (66, 66, 66),
    "minecraft:tuff": (128, 128, 123),
    "minecraft:andesite": (134, 134, 134),
    "minecraft:diorite": (188, 188, 188),
    "minecraft:granite": (143, 92, 78),
    "minecraft:sandstone": (216, 200, 148),
    "minecraft:smooth_sandstone": (221, 206, 151),
    "minecraft:red_sandstone": (194, 93, 58),
    "minecraft:nether_bricks": (42, 22, 20),
    "minecraft:red_nether_bricks": (56, 18, 19),
    "minecraft:purpur_block": (170, 124, 166),
    "minecraft:end_stone": (221, 219, 211),
    "minecraft:obsidian": (21, 14, 29),
    "minecraft:crying_obsidian": (28, 12, 51),
    "minecraft:bedrock": (85, 85, 85),
    "minecraft:clay": (159, 164, 165),
    "minecraft:mud": (59, 50, 46),
    "minecraft:packed_mud": (138, 105, 88),
    "minecraft:dirt": (134, 96, 67),
    "minecraft:coarse_dirt": (119, 85, 59),
    "minecraft:gravel": (131, 126, 126),
    "minecraft:sand": (219, 211, 174),
    "minecraft:red_sand": (191, 110, 62),
    "minecraft:snow": (249, 255, 255),
    "minecraft:ice": (146, 178, 232),
    "minecraft:packed_ice": (144, 170, 220),
    "minecraft:blue_ice": (110, 154, 224),
    "minecraft:slime_block": (126, 203, 69),
    "minecraft:honey_block": (255, 158, 27),
    "minecraft:sea_lantern": (210, 235, 240),
    "minecraft:glowstone": (248, 213, 133),
    "minecraft:shroomlight": (243, 164, 63),
    "minecraft:magma_block": (127, 47, 31),
    "minecraft:soul_sand": (78, 62, 49),
    "minecraft:soul_soil": (78, 55, 40),
    "minecraft:netherrack": (105, 50, 31),
    "minecraft:basalt": (86, 84, 87),
    "minecraft:blackstone": (45, 42, 50),
    "minecraft:gilded_blackstone": (39, 32, 42),
    "minecraft:warped_wart_block": (22, 128, 106),
    "minecraft:nether_wart_block": (114, 7, 7),
    "minecraft:oak_planks": (184, 148, 95),
    "minecraft:spruce_planks": (122, 92, 49),
    "minecraft:birch_planks": (214, 203, 175),
    "minecraft:jungle_planks": (154, 124, 78),
    "minecraft:acacia_planks": (170, 96, 56),
    "minecraft:dark_oak_planks": (74, 48, 30),
    "minecraft:mangrove_planks": (122, 59, 46),
    "minecraft:cherry_planks": (231, 166, 162),
    "minecraft:bamboo_planks": (208, 182, 110),
    "minecraft:crimson_planks": (103, 36, 59),
    "minecraft:warped_planks": (31, 94, 91),
    "minecraft:pumpkin": (222, 142, 26),
    "minecraft:melon": (94, 146, 27),
    "minecraft:hay_block": (165, 133, 27),
    "minecraft:mushroom_stem": (200, 197, 189),
    "minecraft:brown_mushroom_block": (149, 105, 83),
    "minecraft:red_mushroom_block": (176, 50, 37),
    "minecraft:target": (219, 178, 178),
    "minecraft:white_concrete_powder": (207, 207, 207),
    "minecraft:ochre_froglight": (226, 170, 94),
    "minecraft:verdant_froglight": (120, 214, 169),
    "minecraft:pearlescent_froglight": (235, 170, 227),
}

# 不适合用于像素画的方块（会破坏作品完整性）：
#   - 会融化：ice（普通冰，光照下融化）/ packed_ice（浮冰，半透明，如需可自行移除）
#   - 非完整方块（视觉凹陷/厚度不一）：snow（雪层）/ soul_sand
#   - 生存模式无法获取：bedrock
#   - 透明/黏性方块（与玻璃同理，会造成画面噪点）：slime_block / honey_block
# 已保留（不会影响完整性，可按需修改本集合）：
#   - blue_ice（蓝冰，不会融化，保留蓝色系选择）
#   - sand / red_sand / gravel / white_concrete_powder（受重力方块，
#     贴在墙面/地面上放置没有问题，且提供重要配色）
UNSTABLE_BLOCKS = {
    "minecraft:ice", "minecraft:packed_ice",
    "minecraft:snow", "minecraft:soul_sand",
    "minecraft:bedrock",
    "minecraft:slime_block", "minecraft:honey_block",
}


def _drop_unstable(blocks):
    """剔除不适宜用于像素画的方块。"""
    return {k: v for k, v in blocks.items() if k not in UNSTABLE_BLOCKS}


# 按类分组，供 --palette 选择
PALETTE_GROUPS = {
    "auto": {**WOOL, **CONCRETE, **TERRACOTTA, **GLASS, **_drop_unstable(MISC)},
    "wool": WOOL,
    "concrete": CONCRETE,
    "terracotta": TERRACOTTA,
    "glass": GLASS,
    "wool+concrete": {**WOOL, **CONCRETE},
    "concrete+terracotta": {**CONCRETE, **TERRACOTTA},
    "misc": _drop_unstable(MISC),
}

ALL_BLOCKS = PALETTE_GROUPS["auto"]

# 染色玻璃方块 ID（用于玻璃一致性去噪）
GLASS_IDS = set(GLASS.keys())


def get_palette(kind: str = "auto") -> dict:
    kind = (kind or "auto").lower()
    if kind not in PALETTE_GROUPS:
        raise ValueError(
            f"未知调色板: {kind}，可选: {', '.join(PALETTE_GROUPS)}"
        )
    return dict(PALETTE_GROUPS[kind])


def rgb_to_lab(rgb):
    """sRGB → CIE L*a*b* (D65)。返回 (L, a, b)。"""
    r, g, b = [c / 255.0 for c in rgb]
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.0
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    f = lambda t: t ** (1.0 / 3.0) if t > (6.0 / 29.0) ** 3 else (t / (3 * (6.0 / 29.0) ** 2) + 4.0 / 29.0)
    fx, fy, fz = f(x), f(y), f(z)
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def rgb_to_lab_batch(rgb_arr):
    """向量化 sRGB → Lab。rgb_arr: (M, 3) float (0-255)，返回 (M, 3) Lab。"""
    import numpy as np
    rgb = np.asarray(rgb_arr, dtype=np.float64) / 255.0
    mask = rgb > 0.04045
    rgb = np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.0
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    th = (6.0 / 29.0) ** 3
    f = lambda t: np.where(t > th, t ** (1.0 / 3.0), t / (3.0 * (6.0 / 29.0) ** 2) + 4.0 / 29.0)
    fx, fy, fz = f(x), f(y), f(z)
    return np.stack([116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)], axis=1)


def lab_distance(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


class ColorMatcher:
    """把 RGB 颜色匹配到最近的方块颜色。支持 RGB 或 CIE Lab 距离。

    内部用 numpy 预计算调色板并向量化距离计算（比逐像素纯 Python 快百倍）。
    """

    def __init__(self, palette: dict, color_space: str = "lab",
                 glass_bias: float = None, glass_margin: float = 100):
        """color_space: 'lab' 或 'rgb'。

        glass_bias/glass_margin: 玻璃降权门槛。启用后，只有当玻璃的距离同时满足
          best_glass < best_solid * glass_bias  且
          best_glass < best_solid - glass_margin
        时才允许选用玻璃（即玻璃必须明显优于最佳实体方块）。这避免白色/近白色区域
        因为"白色玻璃恰好是纯白"而被匹配成玻璃散点——白色会优先落到雪块/羊毛/混凝土等
        实体方块。传 None 则关闭（保持字面最近色）。
        """
        self.palette = palette
        self.color_space = color_space
        self.ids = list(palette.keys())
        self.glass_bias = glass_bias
        self.glass_margin = glass_margin
        self.glass_set = set(GLASS_IDS) & set(self.ids)
        self.glass_cols = [i for i, bid in enumerate(self.ids) if bid in self.glass_set]
        solid_set = set(range(len(self.ids))) - set(self.glass_cols)
        self.solid_cols = sorted(solid_set)
        try:
            import numpy as np
            self._np = np
            self.rgb_arr = np.array([palette[i] for i in self.ids], dtype=np.float64)
            self.lab_arr = rgb_to_lab_batch(self.rgb_arr) if color_space == "lab" else None
            self.vectorized = True
        except ImportError:
            self.vectorized = False
            self.entries = []
            for block_id, rgb in palette.items():
                entry = {"id": block_id, "rgb": rgb}
                if color_space == "lab":
                    entry["lab"] = rgb_to_lab(rgb)
                self.entries.append(entry)

    def _glass_ok(self, best_glass_d, best_solid_d):
        """玻璃距离 best_glass_d 是否明显优于最佳实体 best_solid_d。"""
        if self.glass_bias is None or best_solid_d is None:
            return True
        return (best_glass_d < best_solid_d * self.glass_bias
                and best_glass_d < best_solid_d - self.glass_margin)

    def match(self, rgb):
        """单像素匹配，返回 (block_id, block_rgb)。"""
        if self.vectorized:
            np = self._np
            px = np.asarray(rgb, dtype=np.float64)
            if self.color_space == "lab":
                lab = rgb_to_lab_batch(px.reshape(1, 3))[0]
                d = ((lab - self.lab_arr) ** 2).sum(axis=1)
            else:
                d = ((px - self.rgb_arr) ** 2).sum(axis=1)
            i = int(d.argmin())
            if self.glass_cols and self.solid_cols:
                gd = float(d[self.glass_cols].min())
                sd = float(d[self.solid_cols].min())
                if self.ids[i] in self.glass_set and not self._glass_ok(gd, sd):
                    i = self.solid_cols[int(d[self.solid_cols].argmin())]
            brgb = self.rgb_arr[i]
            return self.ids[i], (int(brgb[0]), int(brgb[1]), int(brgb[2]))
        best = None
        best_d = None
        lab = None
        if self.color_space == "lab":
            lab = rgb_to_lab(rgb)
        best_g = best_s = None
        best_gd = best_sd = None
        for e in self.entries:
            if self.color_space == "lab":
                d = lab_distance(lab, e["lab"])
            else:
                dr, dg, db = rgb[0] - e["rgb"][0], rgb[1] - e["rgb"][1], rgb[2] - e["rgb"][2]
                d = dr * dr + dg * dg + db * db
            if best_d is None or d < best_d:
                best_d = d
                best = e
            if self.glass_bias is not None:
                if e["id"] in self.glass_set:
                    if best_gd is None or d < best_gd:
                        best_gd, best_g = d, e
                else:
                    if best_sd is None or d < best_sd:
                        best_sd, best_s = d, e
        if (self.glass_bias is not None and best is not None
                and best["id"] in self.glass_set
                and best_s is not None and not self._glass_ok(best_gd, best_sd)):
            best = best_s
        return best["id"], best["rgb"]

    def match_batch(self, rgb_arr):
        """批量匹配。rgb_arr: (M, 3) float，返回 (block_id 列表, 匹配到的 RGB 数组)。"""
        np = self._np
        arr = np.asarray(rgb_arr, dtype=np.float64)
        if self.color_space == "lab":
            lab = rgb_to_lab_batch(arr)
            d = ((lab[:, None, :] - self.lab_arr[None, :, :]) ** 2).sum(axis=2)
        else:
            d = ((arr[:, None, :] - self.rgb_arr[None, :, :]) ** 2).sum(axis=2)
        idx = d.argmin(axis=1)
        if self.glass_cols and self.solid_cols:
            gd = d[:, self.glass_cols].min(axis=1)
            sd = d[:, self.solid_cols].min(axis=1)
            use_glass = (gd < sd * self.glass_bias) & (gd < sd - self.glass_margin)
            glass_chosen = np.isin(idx, np.asarray(self.glass_cols, dtype=np.int64))
            solid_full = np.asarray(self.solid_cols, dtype=np.int64)[
                d[:, self.solid_cols].argmin(axis=1)]
            idx = np.where(glass_chosen & ~use_glass, solid_full, idx)
        ids = [self.ids[i] for i in idx]
        return ids, self.rgb_arr[idx]


def palette_info(palette: dict) -> str:
    """返回调色板统计信息的可读字符串。"""
    return f"{len(palette)} 种方块"
