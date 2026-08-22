# -*- coding: utf-8 -*-
"""Minimal big-endian NBT reader to dump .litematic structure."""
import gzip, io, json, struct, sys

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

NAMES = {0: "TAG_End", 1: "TAG_Byte", 2: "TAG_Short", 3: "TAG_Int", 4: "TAG_Long",
         5: "TAG_Float", 6: "TAG_Double", 7: "TAG_Byte_Array", 8: "TAG_String",
         9: "TAG_List", 10: "TAG_Compound", 11: "TAG_Int_Array", 12: "TAG_Long_Array"}


class NBTReader:
    def __init__(self, data):
        self.buf = data
        self.pos = 0

    def _read(self, n):
        b = self.buf[self.pos:self.pos + n]
        if len(b) < n:
            raise EOFError(f"want {n} bytes, got {len(b)} at {self.pos}")
        self.pos += n
        return b

    def ubyte(self):
        return self._read(1)[0]

    def read(self, fmt, n):
        return struct.unpack(">" + fmt, self._read(n))[0]

    def string(self):
        ln = self.read("H", 2)
        return self._read(ln).decode("utf-8", errors="replace")

    def payload(self, tag):
        t = tag & 0xFF
        if t == TAG_END:
            return None
        if t == TAG_BYTE:
            return struct.unpack(">b", self._read(1))[0]
        if t == TAG_SHORT:
            return self.read("h", 2)
        if t == TAG_INT:
            return self.read("i", 4)
        if t == TAG_LONG:
            return self.read("q", 8)
        if t == TAG_FLOAT:
            return self.read("f", 4)
        if t == TAG_DOUBLE:
            return self.read("d", 8)
        if t == TAG_BYTE_ARRAY:
            n = self.read("i", 4)
            return list(self._read(n))
        if t == TAG_STRING:
            return self.string()
        if t == TAG_LIST:
            et = self.ubyte()
            n = self.read("i", 4)
            return [self.payload(et) for _ in range(n)]
        if t == TAG_COMPOUND:
            out = {}
            while True:
                tt = self.ubyte()
                if tt == TAG_END:
                    break
                name = self.string()
                out[name] = self.payload(tt)
            return out
        if t == TAG_INT_ARRAY:
            n = self.read("i", 4)
            return list(struct.unpack(">" + "i" * n, self._read(4 * n)))
        if t == TAG_LONG_ARRAY:
            n = self.read("i", 4)
            return list(struct.unpack(">" + "q" * n, self._read(8 * n)))
        raise ValueError(f"unknown tag {t}")

    def named_tag(self):
        t = self.ubyte()
        if t == TAG_END:
            return None, None
        name = self.string()
        return name, self.payload(t)


def load(path):
    raw = open(path, "rb").read()
    # try gzip
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    r = NBTReader(raw)
    name, root = r.named_tag()
    return name, root


def summarize(v, depth=0, max_depth=6, key=""):
    pad = "  " * depth
    if isinstance(v, dict):
        if depth >= max_depth:
            return f"{pad}{key}: Compound{{{len(v)} keys}}"
        lines = []
        for k, val in v.items():
            if isinstance(val, dict):
                lines.append(f"{pad}{k}: Compound{{{len(val)} keys}}")
                lines.append(summarize(val, depth + 1, max_depth, ""))
            elif isinstance(val, list):
                if val and isinstance(val[0], dict):
                    lines.append(f"{pad}{k}: List[{len(val)}] of Compound")
                    lines.append(summarize(val[0], depth + 1, max_depth, "[0]"))
                else:
                    first = val[0] if val else None
                    if isinstance(first, (bytes, bytearray)):
                        first = f"<{len(first)} bytes>"
                    lines.append(f"{pad}{k}: List[{len(val)}] of {type(first).__name__} e.g. {str(first)[:60]}")
            else:
                lines.append(f"{pad}{k}: {repr(v)[:80]}")
        return "\n".join(lines)
    return f"{pad}{key}: {repr(v)[:80]}"


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        name, root = load(path)
        print(f"root name: {name}")
        print(summarize(root))
    else:
        print("usage: nbt_dump.py <file>")
