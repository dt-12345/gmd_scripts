from utils import *
import json
from functools import lru_cache
from typing import Dict, List
import base64

@lru_cache
def load_json() -> dict:
    with open("hashes.json", "r") as f:
        return json.load(f)

def write_at_offset(b: bytes, offset: int, stream: WriteStream) -> int:
    pos = stream.tell()
    stream.seek(offset)
    stream.write(b)
    ret = stream.tell()
    stream.seek(pos)
    return ret

gamedata_types: Dict[int, str] = {
    0: "Bool",
    1: "BoolArray",
    2: "Int",
    3: "IntArray",
    4: "Float",
    5: "FloatArray",
    6: "Enum",
    7: "EnumArray",
    8: "Vector2",
    9: "Vector2Array",
    10: "Vector3",
    11: "Vector3Array",
    12: "String16",
    13: "String16Array",
    14: "String32",
    15: "String32Array",
    16: "String64",
    17: "String64Array",
    18: "Binary",
    19: "BinaryArray",
    20: "UInt",
    21: "UIntArray",
    22: "Int64",
    23: "Int64Array",
    24: "UInt64",
    25: "UInt64Array",
    26: "WString16",
    27: "WString16Array",
    28: "WString32",
    29: "WString32Array",
    30: "WString64",
    31: "WString64Array",
    32: "Bool64bitKey"
}

reverse_map: Dict[int, str] = {
    "Bool": 0,
    "BoolArray": 1,
    "Int": 2,
    "IntArray": 3,
    "Float": 4,
    "FloatArray": 5,
    "Enum": 6,
    "EnumArray": 7,
    "Vector2": 8,
    "Vector2Array": 9,
    "Vector3": 10,
    "Vector3Array": 11,
    "String16": 12,
    "String16Array": 13,
    "String32": 14,
    "String32Array": 15,
    "String64": 16,
    "String64Array": 17,
    "Binary": 18,
    "BinaryArray": 19,
    "UInt": 20,
    "UIntArray": 21,
    "Int64": 22,
    "Int64Array": 23,
    "UInt64": 24,
    "UInt64Array": 25,
    "WString16": 26,
    "WString16Array": 27,
    "WString32": 28,
    "WString32Array": 29,
    "WString64": 30,
    "WString64Array": 31,
    "Bool64bitKey": 32
}

class Sav:

    def __init__(self, data: bytes) -> None:
        stream: ReadStream = ReadStream(data)
        self.size = len(data)

        magic = stream.read_u32()
        assert magic == 0x01020304, f"Invalid file magic: {magic}"
        self.format_version = stream.read_u32()
        assert self.format_version in [4710644, 4637640], "Invalid format version - only TotK 1.0.0 through 1.2.1 are supported"

        data_offset: int = stream.read_u32()

        self.offset = data_offset
        
        # Hash section start
        stream.seek(0x20)

        self.datatype: str = "Bool"

        self.save_data = {}

        while stream.tell() < data_offset:
            hash: int = stream.read_u32()
            # flag: str = self.get_flag(hash)
            if not(hash):
                self.datatype = gamedata_types[stream.read_u32()]
            else:
                if self.datatype not in self.save_data:
                    self.save_data[self.datatype] = {}
                match self.datatype:
                    case "Bool":
                        value: bool = bool(stream.read_u32())
                    case "BoolArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            array: bytes = stream.read(4 if count < 32 else int(count / 8 + (1 if count % 8 else 0)))
                            value: List[bool] = []
                            for i in range(count):
                                byte_index: int = int(i // 8)
                                bit_index: int = i % 8
                                value.append(bool(array[byte_index] & (1 << bit_index)))
                            stream.seek(pos)
                    case "Int":
                        value: int = stream.read_s32()
                    case "IntArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[int] = []
                            for i in range(count):
                                value.append(stream.read_s32())
                            stream.seek(pos)
                    case "Float":
                        value: float = stream.read_f32()
                    case "FloatArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[float] = []
                            for i in range(count):
                                value.append(stream.read_f32())
                            stream.seek(pos)
                    case "Enum":
                        value = stream.read_u32()
                    case "EnumArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                # value.append(self.get_array_enum(hex(stream.read_u32()).upper()[2:].zfill(8), hash))
                                value.append(stream.read_u32())
                            stream.seek(pos)
                    case "Vector2":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            value: List[float, float] = [stream.read_f32(), stream.read_f32()]
                            stream.seek(pos)
                    case "Vector2Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[List[float, float]] = []
                            for i in range(count):
                                value.append([stream.read_f32(), stream.read_f32()])
                            stream.seek(pos)
                    case "Vector3":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            value: List[float, float, float] = [stream.read_f32(), stream.read_f32(), stream.read_f32()]
                            stream.seek(pos)
                    case "Vector3Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[List[float, float, float]] = []
                            for i in range(count):
                                value.append([stream.read_f32(), stream.read_f32(), stream.read_f32()])
                            stream.seek(pos)
                    case "String16":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(16)
                            value: str = string[:string.find(b"\x00")].decode("utf-8")
                            stream.seek(pos)
                    case "String16Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(16)
                                string: str = string[:string.find(b"\x00")].decode("utf-8")
                                value.append(string)
                            stream.seek(pos)
                    case "String32":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(32)
                            value: str = string[:string.find(b"\x00")].decode("utf-8")
                            stream.seek(pos)
                    case "String32Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(32)
                                string: str = string[:string.find(b"\x00")].decode("utf-8")
                                value.append(string)
                            stream.seek(pos)
                    case "String64":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(64)
                            value: str = string[:string.find(b"\x00")].decode("utf-8")
                            stream.seek(pos)
                    case "String64Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(64)
                                string: str = string[:string.find(b"\x00")].decode("utf-8")
                                value.append(string)
                            stream.seek(pos)
                    case "Binary":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            size: int = stream.read_u32()
                            value: str = base64.b64encode(stream.read(size).decode())
                            stream.seek(pos)
                    case "BinaryArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                size: int = stream.read_u32()
                                value.append(base64.b64encode(stream.read(size)).decode())
                            stream.seek(pos)
                    case "UInt":
                        value: int = stream.read_u32()
                    case "UIntArray":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[int] = []
                            for i in range(count):
                                value.append(stream.read_u32())
                            stream.seek(pos)
                    case "Int64":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            value: int = stream.read_s64()
                            stream.seek(pos)
                    case "Int64Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[int] = []
                            for i in range(count):
                                value.append(stream.read_s64())
                            stream.seek(pos)
                    case "UInt64":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            value: int = stream.read_u64()
                            stream.seek(pos)
                    case "UInt64Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[int] = []
                            for i in range(count):
                                value.append(stream.read_u64())
                            stream.seek(pos)
                    case "WString16":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(32)
                            value: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                            stream.seek(pos)
                    case "WString16Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(32)
                                string: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                                value.append(string)
                            stream.seek(pos)
                    case "WString32":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(64)
                            value: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                            stream.seek(pos)
                    case "WString32Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(64)
                                string: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                                value.append(string)
                            stream.seek(pos)
                    case "WString64":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            string: bytes = stream.read(128)
                            value: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                            stream.seek(pos)
                    case "WString64Array":
                        offset: int = stream.read_u32()
                        if offset:
                            pos: int = stream.tell()
                            stream.seek(offset)
                            count: int = stream.read_u32()
                            value: List[str] = []
                            for i in range(count):
                                string: bytes = stream.read(128)
                                string: str = string[:string.find(b"\x00\x00") + (string.find(b"\x00\x00") % 2)].decode("utf-16-le")
                                value.append(string)
                            stream.seek(pos)
                    case "Bool64bitKey":
                        offset: int = stream.read_u32()
                        if offset:
                            pos = stream.tell()
                            stream.seek(offset)
                            value: List[int] = []
                            current: int = stream.read_u64()
                            while current:
                                value.append("0x" + hex(current)[2:].zfill(16))
                                current = stream.read_u64()
                            stream.seek(pos)
                self.save_data[self.datatype][hash] = value

    def to_json(self, output: str = '') -> None:
        from os.path import join
        with open(join(output, 'output.json'), 'w', encoding='utf-8') as f:
            json.dump(self.save_data, f, indent=4)

    @staticmethod
    def bool_array_to_bits(array: List[bool]) -> bytes:
        full_bytes = int(len(array) // 8)
        res = b""
        for i in range(full_bytes):
            v = 0
            for j in range(8):
                v |= int(array[i * 8 + j]) << j
            res += v.to_bytes(1)
        v = 0
        for i in range(full_bytes * 8, len(array)):
            v |= int(array[i]) << (i % 8)
        res += v.to_bytes(1)
        return res

    def serialize(self, path: str) -> None:
        with open(path, "wb") as f:
            stream = WriteStream(f)
            stream.write(u32(0x01020304))
            stream.write(u32(self.format_version))
            stream.write(u32(self.offset))
            stream.seek(self.size - 1)
            stream.write(b'\x00')
            stream.seek(0x20)

            offset = self.offset
            for t in self.save_data:
                stream.write(u32(0))
                stream.write(u32(reverse_map[t]))
                for flag in self.save_data[t]:
                    value = self.save_data[t][flag]
                    stream.write(u32(flag))
                    match t:
                        case "Bool":
                            stream.write(u32(1 if value else 0))
                        case "BoolArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                stream.write(Sav.bool_array_to_bits(value))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Int":
                            stream.write(s32(value))
                        case "IntArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(s32(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Float":
                            stream.write(f32(value))
                        case "FloatArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(f32(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Enum":
                            stream.write(u32(value))
                        case "EnumArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(u32(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Vector2":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(f32(value[0]))
                                stream.write(f32(value[1]))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Vector2Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(f32(v[0]))
                                    stream.write(f32(v[1]))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Vector3":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(f32(value[0]))
                                stream.write(f32(value[1]))
                                stream.write(f32(value[2]))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Vector3Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(f32(v[0]))
                                    stream.write(f32(v[1]))
                                    stream.write(f32(v[2]))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String16":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-8")[0:15].ljust(16, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String16Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-8")[0:15].ljust(16, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String32":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-8")[0:31].ljust(32, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String32Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-8")[0:31].ljust(32, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String64":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-8")[0:63].ljust(64, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "String64Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-8")[0:63].ljust(64, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Binary":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                data = base64.b64decode(value)
                                stream.write(u32(len(data)))
                                stream.write(data)
                                stream.align_up(4)
                                offset = stream.tell()
                        case "BinaryArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    data = base64.b64decode(v)
                                    stream.write(u32(len(data)))
                                    stream.write(data)
                                stream.align_up(4)
                                offset = stream.tell()
                        case "UInt":
                            stream.write(u32(value))
                        case "UIntArray":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(u32(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Int64":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(s64(value))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Int64Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(s64(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "UInt64":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u64(value))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "UInt64Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(u64(v))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString16":
                            stream.write(u16(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-16-le")[0:30].ljust(32, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString16Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-16-le")[0:30].ljust(32, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString32":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-16-le")[0:62].ljust(64, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString32Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-16-le")[0:62].ljust(64, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString64":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(value.encode("utf-16-le")[0:126].ljust(128, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "WString64Array":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                stream.write(u32(len(value)))
                                for v in value:
                                    stream.write(v.encode("utf-16-le")[0:126].ljust(128, b"\x00"))
                                stream.align_up(4)
                                offset = stream.tell()
                        case "Bool64bitKey":
                            stream.write(u32(offset))
                            with SeekContext(stream, offset):
                                for v in value:
                                    stream.write(u64(int(v, 16)))
                                stream.write(u64(0))
                                stream.align_up(4)
                                offset = stream.tell()
                        case _:
                            raise ValueError(f"Invalid type {t}")

    @staticmethod
    def apply_diff(diff_path: str, path: str) -> None:
        save = Sav(Path(path).read_bytes())
        diff = json.loads(Path(diff_path).read_text("utf-8"))
        for t in diff:
            if t not in reverse_map:
                raise ValueError(f"Invalid datatype {t}")
            if t not in save.save_data:
                save.save_data[t] = {}
            if t == "Bool64bitKey":
                hash = mmh3.hash("Game", signed=False)
                keys = set(save.save_data[t][hash])
                keys.update(set(diff[t]["Game"]["New"]))
                save.save_data[t][hash] = list(keys - set(diff[t]["Game"]["Old"]))
            if "Array" not in t:
                for flag in diff[t]:
                    if flag.startswith("0x"):
                        hash = int(flag, 16)
                    else:
                        hash = mmh3.hash(flag, signed=False)
                    if diff[t][flag]["New"] is None:
                        del save.save_data[t][hash]
                    else:
                        if "Enum" not in t:
                            save.save_data[t][hash] = diff[t][flag]["New"]
                        else:
                            save.save_data[t][hash] = mmh3.hash(diff[t][flag]["New"], signed=False)
            else:
                for flag in diff[t]:
                    if flag.startswith("0x"):
                        hash = int(flag, 16)
                    else:
                        hash = mmh3.hash(flag, signed=False)
                    for v in diff[t][flag]:
                        if diff[t][flag][v]["New"] is None:
                            raise ValueError("Array resizing is not supported")
                        if int(v) > len(save.save_data[t][hash]) - 1:
                            raise ValueError("Array resizing is not supported")
                        if "Enum" not in t:
                            save.save_data[t][hash][int(v)] = diff[t][flag][v]["New"]
                        else:
                            save.save_data[t][hash][int(v)] = mmh3.hash(diff[t][flag][v]["New"], signed=False)
        save.serialize(path)

from pathlib import Path

hashes: dict = load_json()

def diff(path_1, path_2, out_path = ""):
    out = {}
    save1 = Sav(Path(path_1).read_bytes())
    save2 = Sav(Path(path_2).read_bytes())

    for datatype in save2.save_data:
        if datatype not in save1.save_data:
            for flag in save2.save_data[datatype]:
                name = hashes.get("%08x" % flag, "0x%08x" % flag)
                if name == "???":
                    name = hex(flag)
                out[datatype][name] = {"Old": None, "New": save2.save_data[datatype][flag]}
        else:
            out[datatype] = {}
            for flag in save2.save_data[datatype]:
                if flag not in save1.save_data[datatype]:
                    name = hashes.get("%08x" % flag, "0x%08x" % flag)
                    if name == "???":
                        name = hex(flag)
                    out[datatype][name] = {"Old": None, "New": save2.save_data[datatype][flag]}
                elif save1.save_data[datatype][flag] != save2.save_data[datatype][flag]:
                    name = hashes.get("%08x" % flag, "0x%08x" % flag)
                    if name == "???":
                        name = hex(flag)
                    if "Array" not in datatype and datatype != "Bool64bitKey":
                        if datatype == "Enum":
                            out[datatype][name] = {"Old": hashes["%08x" % save1.save_data[datatype][flag]], "New": hashes["%08x" % save2.save_data[datatype][flag]]}
                        else:
                            out[datatype][name] = {"Old": save1.save_data[datatype][flag], "New": save2.save_data[datatype][flag]}
                    elif datatype == "Bool64bitKey":
                        out[datatype][name] = {"Old": [], "New": []}
                        for key in save2.save_data[datatype][flag]:
                            if key not in save1.save_data[datatype][flag]:
                                out[datatype][name]["New"].append(key)
                    else:
                        out[datatype][name] = {}
                        for i, value in enumerate(save2.save_data[datatype][flag]):
                            if datatype == "EnumArray":
                                value_name = hashes["%08x" % value]
                            else:
                                value_name = value
                            if i >= len(save1.save_data[datatype][flag]):
                                out[datatype][name][i] = {"Old": None, "New": value_name }
                            elif save1.save_data[datatype][flag][i] != value:
                                if datatype == "EnumArray":
                                    out[datatype][name][i] = {"Old": hashes["%08x" % save1.save_data[datatype][flag][i]], "New": value_name}
                                else:
                                    out[datatype][name][i] = {"Old": save1.save_data[datatype][flag][i], "New": value_name}
            if out[datatype] == {}:
                del out[datatype]
    for datatype in save1.save_data:
        if datatype not in save2.save_data:
            for flag in save1.save_data[datatype]:
                name = hashes.get("%08x" % flag, "0x%08x" % flag)
                if name == "???":
                    name = hex(flag)
                out[datatype][name] = {"Old": save1.save_data[datatype][flag], "New": None}
        else:
            if datatype not in out:
                out[datatype] = {}
            for flag in save1.save_data[datatype]:
                if flag not in save2.save_data[datatype]:
                    name = hashes.get("%08x" % flag, "0x%08x" % flag)
                    if name == "???":
                        name = hex(flag)
                    out[datatype][name] = {"Old": save1.save_data[datatype][flag], "New": None}
                elif save2.save_data[datatype][flag] != save1.save_data[datatype][flag]:
                    name = hashes.get("%08x" % flag, "0x%08x" % flag)
                    if name == "???":
                        name = hex(flag)
                    if name in out[datatype]:
                        pass
                    if "Array" not in datatype and datatype != "Bool64bitKey":
                        if datatype == "Enum":
                            out[datatype][name] = {"Old": hashes["%08x" % save1.save_data[datatype][flag]], "New": hashes["%08x" % save2.save_data[datatype][flag]]}
                        else:
                            out[datatype][name] = {"Old": save1.save_data[datatype][flag], "New": save2.save_data[datatype][flag]}
                    elif datatype == "Bool64bitKey":
                        if name not in out[datatype]:
                            out[datatype][name] = {}
                        out[datatype][name]["Old"] = []
                        for key in save2.save_data[datatype][flag]:
                            if key not in save1.save_data[datatype][flag]:
                                out[datatype][name]["Old"].append(key)
                    else:
                        if name not in out[datatype]:
                            out[datatype][name] = {}
                        for i, value in enumerate(save1.save_data[datatype][flag]):
                            if i in out[datatype][name]:
                                continue
                            if datatype == "EnumArray":
                                value_name = hashes["%08x" % value]
                            else:
                                value_name = value
                            if i >= len(save2.save_data[datatype][flag]):
                                out[datatype][name][i] = {"Old": value_name, "New": None}
                            elif save2.save_data[datatype][flag][i] != value:
                                if datatype == "EnumArray":
                                    out[datatype][name][i] = {"Old": value_name, "New": hashes["%08x" % save2.save_data[datatype][flag][i]]}
                                else:
                                    out[datatype][name][i] = {"Old": value_name, "New": save2.save_data[datatype][flag][i]}
            if out[datatype] == {}:
                del out[datatype]
    
    if out_path == "":
        with open("diff.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=4, ensure_ascii=False)
    else:
        import os
        os.makedirs(out_path, exist_ok=True)
        with open(os.path.join(out_path, "diff.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # import shutil
    # import os

    # ryu_path = os.path.join(os.getenv("APPDATA"), "Ryujinx/bis/user/save/0000000000000001")

    # # diff("SAVES/slot_01/progress.sav", os.path.join(ryu_path, "0/slot_05/progress.sav"))

    # # shutil.copytree("SAVES", "SAVES_FIXED", dirs_exist_ok=True)

    # # for dir, subdir, files in os.walk("SAVES"):
    # #     for file in files:
    # #         if file == "progress.sav":
    # #             path = os.path.join(dir, file)
    # #             assert os.path.exists(path)
    # #             Sav.apply_diff("diff.json", path.replace("SAVES/", ""))

    # try:
    #     os.remove("progress.sav")
    # except:
    #     pass

    # shutil.copyfile("SAVES/slot_01/progress.sav", "progress.sav")

    # Sav.apply_diff("diff.json", "progress.sav")

    # shutil.copyfile("progress.sav", os.path.join(ryu_path, "0", "slot_00", "progress.sav"))
    # shutil.copyfile("progress.sav", os.path.join(ryu_path, "1", "slot_00", "progress.sav"))

    # # diff("progress.sav", os.path.join(ryu_path, "0/slot_05/progress.sav"), "result")

    path_to_your_file = ""

    file = Sav(Path(path_to_your_file).read_bytes)
    file.to_json("progress.json")