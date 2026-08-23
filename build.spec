# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 可复现构建脚本 —— 一条命令同时生成 GUI + 命令行两个单文件 exe。

用法（在项目根目录执行）:
    pip install pyinstaller
    pyinstaller build.spec          # 产物输出到 dist/
    # 或按平台追加: --clean --noconfirm

与《打包说明.md》里的命令等价:
    图形界面版: --onefile --windowed --name 图片转MC像素画投影         --icon app_icon.ico main.py
    命令行版:   --onefile --console   --name 图片转MC像素画投影_命令行 --icon app_icon.ico cli.py

说明: 本 spec 使用 PyInstaller 注入的全局 (Analysis / PYZ / EXE / SPECPATH),
由 PyInstaller 执行时直接可用，无需手动 import。
"""
import os

ROOT = SPECPATH  # PyInstaller 注入：spec 文件所在目录（即项目根）


def build_exe(name, entry_script, console):
    """构建一个单文件 (onefile) exe。"""
    a = Analysis(
        [os.path.join(ROOT, entry_script)],
        pathex=[ROOT],
        binaries=[],
        datas=[],
        hiddenimports=[],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        noarchive=False,
    )
    pyz = PYZ(a.pure)
    EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        icon=os.path.join(ROOT, "app_icon.ico"),
    )


# 图形界面版（无控制台窗口）
build_exe("图片转MC像素画投影", "main.py", console=False)

# 命令行版（保留控制台，便于脚本/批处理）
build_exe("图片转MC像素画投影_命令行", "cli.py", console=True)
