# -*- coding: utf-8 -*-
"""GUI 多语言文案表（供 main.py 使用）。

语言: 'zh'（默认，简体中文）或 'en'（English）。

用法:
    from i18n import tr
    tr("控制面板", lang)        # lang='en' 时返回英文，否则返回原文
"""

LANGS = ("zh", "en")

# 静态 UI 文案：中文原文 -> 英文
TEXT = {
    # 窗口标题 / 面板
    "图片 → 像素画 → Minecraft投影 生成器": "Image → Pixel Art → Minecraft Projection Generator",
    "控制面板": "Control Panel",
    "语言:": "Language:",

    # 行0
    "① 选择图片...": "① Select Image...",
    "未选择图片": "No image selected",
    "输出目录:": "Output folder:",
    "选择…": "Browse…",

    # 行1 阶段1
    "阶段1 像素尺寸:": "Stage 1 pixel size:",
    "宽:": "Width:",
    "高:": "Height:",
    "保持宽高比": "Keep aspect ratio",
    "自定义": "Custom",

    # 行2 背景
    "背景处理:": "Background:",
    "背景:自动(白色)": "Background: auto (white)",
    "取样背景色": "Sample bg color",
    "重置": "Reset",
    "① 生成像素画": "① Generate Pixel Art",
    "② 生成MC投影": "② Generate MC Projection",
    "一键生成全部": "Generate All",

    # 行3 阶段2
    "MC调色板:": "MC Palette:",
    "抖动:": "Dither:",
    "颜色:": "Color:",
    "放大scale:": "Scale:",
    "厚度:": "Thickness:",
    "背面填充:": "Backing:",

    # 行4
    "原点X Y Z:": "Origin X Y Z:",
    "名称:": "Name:",
    "作者:": "Author:",
    "朝向:": "Orientation:",
    "竖放(墙面/平视)": "Wall (vertical / front)",
    "横放(地面/俯视)": "Floor (horizontal / top-down)",
    "导出:": "Export:",
    "纯像素画PNG": "Pixel Art PNG",
    "打开输出文件夹": "Open output folder",

    # 行5
    "显示网格": "Show grid",
    "像素画格子:": "Pixel cell:",
    "MC预览格子:": "MC cell:",

    # 画布标题 / 底部信息 / 状态
    "左：像素画（点击格子取样背景色）": "Left: Pixel art (click a cell to sample bg color)",
    "右：Minecraft 方块预览": "Right: Minecraft block preview",
    "尚未生成像素画": "No pixel art yet",
    "请选择一张图片开始": "Select an image to start",

    # 组合框选项（背景）
    "无": "None",
    "去除背景(镂空)": "Remove background (carve-out)",
    "背景填玻璃": "Glass background",

    # 组合框选项（调色板）
    "auto（全部149种）": "auto (all 149)",
    "wool（羊毛）": "wool",
    "concrete（混凝土）": "concrete",
    "terracotta（陶瓦）": "terracotta",
    "glass（玻璃）": "glass",
    "misc（建材）": "misc (blocks)",

    # 组合框选项（抖动）
    "floyd（抖动，渐变平滑）": "floyd (dithered)",
    "none（纯色）": "none (solid)",

    # 常见信息
    "提示": "Hint",
    "错误": "Error",
    "完成": "Done",
    "请先选择一张图片": "Please select an image first",
    "正在处理中，请稍候…": "Processing, please wait…",
    "请先点击「① 生成像素画」": "Please click ① Generate Pixel Art first",
    "自定义宽高需为 1~4096 的整数": "Custom width/height must be integers 1–4096",
    "放大倍数/厚度/原点必须是整数": "Scale/thickness/origin must be integers",
    "请先点击「① 生成像素画」，然后点击左侧图纸中的背景格子取样背景色":
        "Please click ① Generate Pixel Art first, then click a background cell on the left to sample its color",
    "请点击左侧像素画中的【背景格子】取样背景色（背景处理选「去除背景」或「背景填玻璃」后生效）":
        "Click a background cell on the left to sample bg color (works with Remove background or Glass background)",
    "请先生成像素画，再点击图纸取样背景色": "Generate pixel art first, then click the canvas to sample bg color",
    "该位置为空白，请点击实心格子取样背景色": "That cell is empty; please click a filled cell",
    "若背景处理选「去除背景」或「背景填玻璃」，取样色将用于识别背景":
        "The sampled color is used for background detection (Remove / Glass background modes)",
    "请先选择一张图片开始": "Select an image to start",
    "导出纯像素画 PNG（每格=1px）": "Export pure pixel art PNG (1px = 1 cell)",
    "PNG 图片": "PNG image",
    "后台正在生成…": "Generating in background…",

    # 面板 / 弹窗标题
    "像素画信息": "Pixel Art Info",
    "选择图片": "Select Image",
    "图片文件": "Image files",
    "所有文件": "All files",
    "打开失败": "Open failed",
    "选择输出文件夹": "Select output folder",
    "导出失败": "Export failed",
    "导出成功": "Exported",
    "程序启动失败": "Startup failed",

    # 后台任务名 / 进度
    "生成像素画": "Generate Pixel Art",
    "生成MC投影": "Generate MC Projection",
    "一键生成": "Generate All",
    "准备中…": "Preparing…",
    "阶段1完成": "Stage 1 done",
    "失败": "Failed",
}


def tr(text, lang):
    """按语言返回文案。lang='en' 时返回英文；否则返回原文。"""
    if lang == "en":
        return TEXT.get(text, text)
    return text
