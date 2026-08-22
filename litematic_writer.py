# -*- coding: utf-8 -*-
"""自包含的 .litematic (Litematica 原理图) v7 格式写出器。

格式要点（已通过示例文件、litemapy 源码、litematica mod 字节码三重验证）：
- 文件 = gzip 压缩的 big-endian NBT
- 根标签: MinecraftDataVersion / Version=7 / SubVersion=1 / Metadata / Regions
- Region:
    Position / Size / BlockStatePalette / BlockStates / Entities / TileEntities
    / PendingBlockTicks / PendingFluidTicks
- BlockStates 是 LongArray：每个方块位宽 bits = max(2, ceil(log2(palette 大小)))，
  从最低位(LSB)开始打包；线性索引 index = y*(W*L) + z*W + x（x 最快）。
"""
from __future__ import annotations

import gzip
import math
import struct
import time


# ---------- NBT 标签类型 ----------
TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class NBT:
    """NBT 标签基类。"""

    def __init__(self, value):
        self.value = value

    def tag_type(self):
        raise NotImplementedError

    def write_payload(self, buf):
        raise NotImplementedError


class NBTCompound(NBT):
    def __init__(self, pairs=None):
        super().__init__(dict(pairs or {}))

    def tag_type(self):
        return TAG_COMPOUND

    def __setitem__(self, key, value):
        self.value[key] = value

    def __getitem__(self, key):
        return self.value[key]

    def write_payload(self, buf):
        for key, val in self.value.items():
            buf.append(struct.pack(">B", val.tag_type()))
            write_string(buf, key)
            val.write_payload(buf)
        buf.append(struct.pack(">B", TAG_END))


class NBTList(NBT):
    def __init__(self, items, elem_type):
        super().__init__(list(items))
        self.elem_type = elem_type

    def tag_type(self):
        return TAG_LIST

    def write_payload(self, buf):
        buf.append(struct.pack(">B", self.elem_type))
        buf.append(struct.pack(">i", len(self.value)))
        for item in self.value:
            item.write_payload(buf)


class NBTInt(NBT):
    def tag_type(self):
        return TAG_INT

    def write_payload(self, buf):
        buf.append(struct.pack(">i", int(self.value)))


class NBTLong(NBT):
    def tag_type(self):
        return TAG_LONG

    def write_payload(self, buf):
        buf.append(struct.pack(">q", int(self.value)))


class NBTShort(NBT):
    def tag_type(self):
        return TAG_SHORT

    def write_payload(self, buf):
        buf.append(struct.pack(">h", int(self.value)))


class NBTByte(NBT):
    def tag_type(self):
        return TAG_BYTE

    def write_payload(self, buf):
        buf.append(struct.pack(">b", int(self.value)))


class NBTString(NBT):
    def tag_type(self):
        return TAG_STRING

    def write_payload(self, buf):
        write_string(buf, str(self.value))


class NBTLongArray(NBT):
    def tag_type(self):
        return TAG_LONG_ARRAY

    def write_payload(self, buf):
        vals = list(self.value)
        buf.append(struct.pack(">i", len(vals)))
        for v in vals:
            buf.append(struct.pack(">q", int(v)))


def write_string(buf, s):
    data = s.encode("utf-8")
    buf.append(struct.pack(">H", len(data)))
    buf.append(data)


def write_named_tag(buf, name, tag):
    buf.append(struct.pack(">B", tag.tag_type()))
    write_string(buf, name)
    tag.write_payload(buf)


# ---------- 方块状态 ----------
class BlockState:
    """一个方块状态：'minecraft:white_concrete' 或带属性 'minecraft:xxx[prop=val,...]'。"""

    def __init__(self, name: str, properties: dict = None):
        self.name = name
        self.properties = dict(properties or {})

    def to_nbt(self) -> NBTCompound:
        tag = NBTCompound()
        tag["Name"] = NBTString(self.name)
        if self.properties:
            props = NBTCompound()
            for k, v in self.properties.items():
                props[k] = NBTString(str(v))
            tag["Properties"] = props
        return tag

    def __repr__(self):
        return self.name + (f"{self.properties}" if self.properties else "")


AIR = BlockState("minecraft:air")


# ---------- 位打包 ----------
def pack_block_states(states: list, palette: list):
    """把方块索引列表打包成 LSB-first 的 64 位长整型数组。

    :param states:  长度 = W*H*L 的调色板索引列表（线性顺序见 RegionBuilder）
    :param palette: 调色板（方块状态列表）
    """
    nbits = max(2, math.ceil(math.log2(len(palette))))
    mask64 = (1 << 64) - 1
    mask = (1 << nbits) - 1
    n_longs = math.ceil(len(states) * nbits / 64)
    longs = [0] * n_longs
    for i, s in enumerate(states):
        start = i * nbits
        li = start >> 6
        bo = start & 63
        longs[li] = (longs[li] | ((s & mask) << bo)) & mask64
        if bo + nbits > 64:
            longs[li + 1] = (longs[li + 1] | ((s & mask) >> (64 - bo))) & mask64
    # 转成有符号（NBT Long 存储，最高位置 1 的数值在 Java 里是负数）
    signed = [v - (1 << 64) if v & (1 << 63) else v for v in longs]
    return NBTLongArray(signed), nbits


# ---------- Region 构建器 ----------
class RegionBuilder:
    """收集方块并生成一个 Region 的 NBT 标签。

    局部坐标: x∈[0,W), y∈[0,H), z∈[0,L)，世界坐标 = origin + 局部坐标（正尺寸）。
    """

    def __init__(self, name: str, origin=(0, 0, 0), size=(0, 0, 0)):
        self.name = name
        self.origin = origin
        self.size = size  # (W, H, L) 全部为正
        self.palette = [AIR]
        self.palette_index = {AIR.name: 0}
        self.blocks = {}  # (x, y, z) -> palette index

    def _palette_id(self, block: BlockState):
        key = (block.name, tuple(sorted(block.properties.items())))
        if key not in self.palette_index:
            self.palette_index[key] = len(self.palette)
            self.palette.append(block)
        return self.palette_index[key]

    def set_block(self, x, y, z, block: BlockState):
        """x,y,z 为世界坐标（相对 origin 之外直接给绝对坐标也可以，内部会转换）。"""
        ox, oy, oz = self.origin
        lx, ly, lz = x - ox, y - oy, z - oz
        if not (0 <= lx < self.size[0] and 0 <= ly < self.size[1] and 0 <= lz < self.size[2]):
            raise ValueError(
                f"方块 ({x},{y},{z}) 超出区域范围 origin={self.origin} size={self.size}"
            )
        if block.name == AIR.name and not block.properties:
            self.blocks.pop((lx, ly, lz), None)
            return
        self.blocks[(lx, ly, lz)] = self._palette_id(block)

    def build(self) -> NBTCompound:
        W, H, L = self.size
        volume = W * H * L
        states = [0] * volume
        for (lx, ly, lz), pid in self.blocks.items():
            ind = ly * (W * L) + lz * W + lx
            states[ind] = pid
        arr, nbits = pack_block_states(states, self.palette)

        tag = NBTCompound()
        pos = NBTCompound()
        pos["x"] = NBTInt(self.origin[0])
        pos["y"] = NBTInt(self.origin[1])
        pos["z"] = NBTInt(self.origin[2])
        tag["Position"] = pos
        size = NBTCompound()
        size["x"] = NBTInt(W)
        size["y"] = NBTInt(H)
        size["z"] = NBTInt(L)
        tag["Size"] = size
        tag["BlockStatePalette"] = NBTList([b.to_nbt() for b in self.palette], TAG_COMPOUND)
        tag["BlockStates"] = arr
        tag["Entities"] = NBTList([], TAG_COMPOUND)
        tag["TileEntities"] = NBTList([], TAG_COMPOUND)
        tag["PendingBlockTicks"] = NBTList([], TAG_COMPOUND)
        tag["PendingFluidTicks"] = NBTList([], TAG_COMPOUND)
        return tag


# ---------- Schematic ----------
class Schematic:
    def __init__(self, name="像素画", author="", description="", mc_data_version=3955):
        self.name = name
        self.author = author
        self.description = description
        self.mc_data_version = mc_data_version
        self.regions = {}  # name -> RegionBuilder

    def add_region(self, region: RegionBuilder):
        self.regions[region.name] = region

    def to_nbt(self) -> NBTCompound:
        now = int(time.time() * 1000)
        total_volume = 0
        total_blocks = 0
        min_x = min_y = min_z = None
        max_x = max_y = max_z = None

        regions_tag = NBTCompound()
        for rname, reg in self.regions.items():
            regions_tag[rname] = reg.build()
            ox, oy, oz = reg.origin
            W, H, L = reg.size
            total_volume += W * H * L
            total_blocks += len(reg.blocks)
            for (px, py, pz) in [
                (ox, oy, oz), (ox + W - 1, oy + H - 1, oz + L - 1),
            ]:
                if min_x is None:
                    min_x, min_y, min_z = px, py, pz
                    max_x, max_y, max_z = px, py, pz
                else:
                    min_x, min_y, min_z = min(min_x, px), min(min_y, py), min(min_z, pz)
                    max_x, max_y, max_z = max(max_x, px), max(max_y, py), max(max_z, pz)

        meta = NBTCompound()
        meta["TimeCreated"] = NBTLong(now)
        meta["TimeModified"] = NBTLong(now)
        enc = NBTCompound()
        enc["x"] = NBTInt(max_x - min_x + 1)
        enc["y"] = NBTInt(max_y - min_y + 1)
        enc["z"] = NBTInt(max_z - min_z + 1)
        meta["EnclosingSize"] = enc
        meta["Description"] = NBTString(self.description)
        meta["RegionCount"] = NBTInt(len(self.regions))
        meta["TotalBlocks"] = NBTInt(total_blocks)
        meta["Author"] = NBTString(self.author)
        meta["TotalVolume"] = NBTInt(total_volume)
        meta["Name"] = NBTString(self.name)

        root = NBTCompound()
        root["MinecraftDataVersion"] = NBTInt(self.mc_data_version)
        root["Version"] = NBTInt(7)
        root["Metadata"] = meta
        root["Regions"] = regions_tag
        root["SubVersion"] = NBTInt(1)
        return root

    def save(self, path: str):
        root = self.to_nbt()
        buf = [struct.pack(">B", TAG_COMPOUND)]
        write_string(buf, "")
        root.write_payload(buf)
        data = b"".join(buf)
        with open(path, "wb") as f:
            f.write(gzip.compress(data, compresslevel=6))
        return len(data)
