# -*- coding: utf-8 -*-
"""Minecraft 方块中文名对照表（用于材料清单 Excel）。

覆盖 mc_palette.py 中全部方块（含已剔除的、以及空气）。命名参照 Minecraft
简体中文官方译名。未收录的方块回退显示为英文 ID。
"""
from __future__ import annotations

# 16 色羊毛
_WOOL = {
    "white_wool": "白色羊毛", "orange_wool": "橙色羊毛", "magenta_wool": "品红色羊毛",
    "light_blue_wool": "淡蓝色羊毛", "yellow_wool": "黄色羊毛", "lime_wool": "黄绿色羊毛",
    "pink_wool": "粉红色羊毛", "gray_wool": "灰色羊毛", "light_gray_wool": "淡灰色羊毛",
    "cyan_wool": "青色羊毛", "purple_wool": "紫色羊毛", "blue_wool": "蓝色羊毛",
    "brown_wool": "棕色羊毛", "green_wool": "绿色羊毛", "red_wool": "红色羊毛",
    "black_wool": "黑色羊毛",
}
# 16 色混凝土
_CONCRETE = {
    "white_concrete": "白色混凝土", "orange_concrete": "橙色混凝土",
    "magenta_concrete": "品红色混凝土", "light_blue_concrete": "淡蓝色混凝土",
    "yellow_concrete": "黄色混凝土", "lime_concrete": "黄绿色混凝土",
    "pink_concrete": "粉红色混凝土", "gray_concrete": "灰色混凝土",
    "light_gray_concrete": "淡灰色混凝土", "cyan_concrete": "青色混凝土",
    "purple_concrete": "紫色混凝土", "blue_concrete": "蓝色混凝土",
    "brown_concrete": "棕色混凝土", "green_concrete": "绿色混凝土",
    "red_concrete": "红色混凝土", "black_concrete": "黑色混凝土",
}
# 16 色陶瓦
_TERRACOTTA = {
    "white_terracotta": "白色陶瓦", "orange_terracotta": "橙色陶瓦",
    "magenta_terracotta": "品红色陶瓦", "light_blue_terracotta": "淡蓝色陶瓦",
    "yellow_terracotta": "黄色陶瓦", "lime_terracotta": "黄绿色陶瓦",
    "pink_terracotta": "粉红色陶瓦", "gray_terracotta": "灰色陶瓦",
    "light_gray_terracotta": "淡灰色陶瓦", "cyan_terracotta": "青色陶瓦",
    "purple_terracotta": "紫色陶瓦", "blue_terracotta": "蓝色陶瓦",
    "brown_terracotta": "棕色陶瓦", "green_terracotta": "绿色陶瓦",
    "red_terracotta": "红色陶瓦", "black_terracotta": "黑色陶瓦",
}
# 16 色染色玻璃
_GLASS = {
    "white_stained_glass": "白色染色玻璃", "orange_stained_glass": "橙色染色玻璃",
    "magenta_stained_glass": "品红色染色玻璃", "light_blue_stained_glass": "淡蓝色染色玻璃",
    "yellow_stained_glass": "黄色染色玻璃", "lime_stained_glass": "黄绿色染色玻璃",
    "pink_stained_glass": "粉红色染色玻璃", "gray_stained_glass": "灰色染色玻璃",
    "light_gray_stained_glass": "淡灰色染色玻璃", "cyan_stained_glass": "青色染色玻璃",
    "purple_stained_glass": "紫色染色玻璃", "blue_stained_glass": "蓝色染色玻璃",
    "brown_stained_glass": "棕色染色玻璃", "green_stained_glass": "绿色染色玻璃",
    "red_stained_glass": "红色染色玻璃", "black_stained_glass": "黑色染色玻璃",
}
# 建材/装饰方块
_MISC = {
    "quartz_block": "石英块", "smooth_quartz": "平滑石英块", "snow_block": "雪块",
    "bone_block": "骨块", "calcite": "方解石",
    "white_glazed_terracotta": "白色带釉陶瓦", "gold_block": "金块",
    "iron_block": "铁块", "diamond_block": "钻石块", "emerald_block": "绿宝石块",
    "lapis_block": "青金石块", "redstone_block": "红石块", "coal_block": "煤炭块",
    "netherite_block": "下界合金块", "copper_block": "铜块", "exposed_copper": "斑驳的铜块",
    "weathered_copper": "风化的铜块", "oxidized_copper": "氧化的铜块",
    "amethyst_block": "紫水晶块", "stone": "石头", "cobblestone": "圆石",
    "mossy_cobblestone": "苔石", "stone_bricks": "石砖", "cracked_stone_bricks": "裂纹石砖",
    "mossy_stone_bricks": "苔石砖", "chiseled_stone_bricks": "錾制石砖",
    "bricks": "砖块", "deepslate": "深板岩", "cobbled_deepslate": "深板岩圆石",
    "deepslate_bricks": "深板岩砖", "tuff": "凝灰岩", "andesite": "安山岩",
    "diorite": "闪长岩", "granite": "花岗岩", "sandstone": "砂岩",
    "smooth_sandstone": "平滑砂岩", "red_sandstone": "红砂岩",
    "nether_bricks": "下界砖块", "red_nether_bricks": "红色下界砖块",
    "purpur_block": "紫珀块", "end_stone": "末地石", "obsidian": "黑曜石",
    "crying_obsidian": "哭泣的黑曜石", "clay": "黏土块", "mud": "泥巴",
    "packed_mud": "泥坯", "dirt": "泥土", "coarse_dirt": "砂土", "gravel": "沙砾",
    "sand": "沙子", "red_sand": "红沙", "snow": "雪", "ice": "冰",
    "packed_ice": "浮冰", "blue_ice": "蓝冰", "slime_block": "黏液块",
    "honey_block": "蜂蜜块", "sea_lantern": "海晶灯", "glowstone": "萤石",
    "shroomlight": "菌光体", "magma_block": "岩浆块", "soul_sand": "灵魂沙",
    "soul_soil": "灵魂土", "netherrack": "下界岩", "basalt": "玄武岩",
    "blackstone": "黑石", "gilded_blackstone": "镶金黑石",
    "warped_wart_block": "诡异疣块", "nether_wart_block": "下界疣块",
    "oak_planks": "橡木木板", "spruce_planks": "云杉木板", "birch_planks": "白桦木板",
    "jungle_planks": "丛林木板", "acacia_planks": "金合欢木板",
    "dark_oak_planks": "深色橡木木板", "mangrove_planks": "红树木板",
    "cherry_planks": "樱花木板", "bamboo_planks": "竹木板",
    "crimson_planks": "绯红木板", "warped_planks": "诡异木板",
    "pumpkin": "南瓜", "melon": "西瓜", "hay_block": "干草块",
    "mushroom_stem": "蘑菇柄", "brown_mushroom_block": "棕色蘑菇方块",
    "red_mushroom_block": "红色蘑菇方块", "target": "标靶",
    "white_concrete_powder": "白色混凝土粉末",
    "ochre_froglight": "赭黄蛙明灯", "verdant_froglight": "翠绿蛙明灯",
    "pearlescent_froglight": "珠光蛙明灯", "bedrock": "基岩",
}

# 完整对照表（去掉 minecraft: 前缀的键）
_BY_NAME = {**_WOOL, **_CONCRETE, **_TERRACOTTA, **_GLASS, **_MISC}
BLOCK_CN = {"minecraft:" + k: v for k, v in _BY_NAME.items()}
BLOCK_CN["minecraft:air"] = "空气"


def cn_name(block_id: str) -> str:
    """返回方块 ID 的中文名；未收录时回退为英文 ID（去掉 minecraft: 前缀）。"""
    name = BLOCK_CN.get(block_id)
    if name:
        return name
    return block_id.replace("minecraft:", "")


def cn_name_full(block_id: str) -> str:
    """中文名 + 英文 ID，如 "白色羊毛 (white_wool)"。"""
    return f"{cn_name(block_id)} ({block_id.replace('minecraft:', '')})"


def en_name(block_id: str) -> str:
    """方块 ID -> 人类可读英文名（如 minecraft:white_wool -> White Wool）。"""
    key = block_id.replace("minecraft:", "")
    return key.replace("_", " ").title()
