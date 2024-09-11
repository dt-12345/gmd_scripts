import byml
import zstd
import os
import json
import math
from pathlib import Path
try:
    import mmh3
except ImportError:
    raise ImportError("mmh3 not found - try running pip install mmh3 then try again")

valid_types = [
    "Bool",
    "BoolArray",
    "Int",
    "IntArray",
    "Float",
    "FloatArray",
    "Enum",
    "EnumArray",
    "Vector2",
    "Vector2Array",
    "Vector3",
    "Vector3Array",
    "String16",
    "String16Array",
    "String32",
    "String32Array",
    "String64",
    "String64Array",
    "Binary",
    "BinaryArray",
    "UInt",
    "UIntArray",
    "Int64",
    "Int64Array",
    "UInt64",
    "UInt64Array",
    "WString16",
    "WString16Array",
    "WString32",
    "WString32Array",
    "WString64",
    "WString64Array",
    "Struct",
    "BoolExp",
    "Bool64bitKey"
]

reset_types = [
    "cOnSceneChange",
    "cOnGameDayChange",
    "cOptionReset",
    "cOnBloodyMoon",
    "cOnStartNewData",
    "cOnGameDayChangeRandom",
    "cOnSceneInitialize",
    "cZonauEnemyRespawnTimer",
    "cRandomRevival",
    "cOnStartNewDataOnly"
]

letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']

class GameData:
    def __init__(self, gamedata_path, romfs_path=""):
        print("Initializing GameData")
        try:
            self._ctx = zstd.ZstdDecompContext(os.path.join(romfs_path, "Pack/ZsDic.pack.zs"))
        except:
            raise Exception("Error initializing Zstd decompression context")
        try:
            self._byml = byml.Byml(self._ctx.decompress(gamedata_path), os.path.basename(gamedata_path).replace(".zs", ""))
        except:
            raise Exception("Error reading GameDataList file")
        with open("hashes.json", "r", encoding="utf-8") as f:
            self._hashes = json.load(f)
        print("Initialized")
    
    def GetFlagByHash(self, hash, datatype):
        assert datatype in valid_types, f"Invalid GameData flag type: {datatype}"
        if isinstance(hash, str):
            hash = int(hash, 16)
        if datatype not in self._byml.root_node["Data"]:
            return None
        for flag in self._byml.root_node["Data"][datatype]:
            if hash == flag["Hash"]:
                return flag
        return None
    
    def GetFlagByName(self, flagname, datatype):
        hash = mmh3.hash(flagname, signed=False)
        return self.GetFlagByHash(hash, datatype)
    
    def AddFlag(self, new_flag, datatype, validate=True):
        assert datatype in valid_types, f"Invalid GameData flag type: {datatype}"
        if validate:
            new_flag = self.ValidateFlag(new_flag, datatype)
        if datatype not in self._byml.root_node["Data"]:
            self._byml.root_node["Data"][datatype] = []
            self._byml.root_node["Data"][datatype].append(new_flag)
            return
        for i, flag in enumerate(self._byml.root_node["Data"][datatype]):
            if new_flag["Hash"] == flag["Hash"]:
                self._byml.root_node["Data"][datatype][i] = new_flag
                return
        self._byml.root_node["Data"][datatype].append(new_flag)
        return
    
    def DeleteFlagByHash(self, hash, datatype):
        assert datatype in valid_types, f"Invalid GameData flag type: {datatype}"
        if datatype not in self._byml.root_node["Data"]:
            return 0
        for i, flag in enumerate(self._byml.root_node["Data"][datatype]):
            if hash == flag["Hash"]:
                self._byml.root_node["Data"][datatype].pop(i)
                return 1
        return 0
    
    def DeleteFlagByName(self, flagname, datatype):
        hash = mmh3.hash(flagname, signed=False)
        return self.DeleteFlagByHash(hash, datatype)
    
    def Serialize(self, output_dir=""):
        if output_dir != "":
            os.makedirs(output_dir, exist_ok=True)
        if "Bool64bitKey" in self._byml.root_node["Data"]:
            self._byml.root_node["Data"]["Bool64bitKey"] = sorted(self._byml.root_node["Data"]["Bool64bitKey"], key=lambda d: d["Hash"])
        self.UpdateMetaData()
        print("Serializing...")
        self._byml.Reserialize(output_dir)
        print("Finished!")

    @staticmethod
    def CalcResetTypeValue(*types):
        value = 0
        for reset_type in types:
            if reset_type in reset_types:
                value |= (2 ** reset_types.index(reset_type))
        return byml.Int(value)
    
    @staticmethod
    def GetResetTypes(value):
        types = []
        for i in range(len(reset_types)):
            if value & (2 ** i):
                types.append(reset_types[i])
        return types
    
    @staticmethod
    def CalcExtraByte(map_unit):
        if len(map_unit) != 2 or not(isinstance(map_unit, str)):
            raise ValueError("Invalid map unit - should be in a form such as F5")
        if map_unit[0] not in letters:
            raise ValueError("Out of range (A1 - J8)")
        if not(map_unit[1].isdigit()) or int(map_unit[1]) not in range(9):
            raise ValueError("Out of range (A1 - J8)")
        return byml.Int(letters.index(map_unit[0]) + 10 * (int(map_unit[1]) - 1) + 1)
    
    @staticmethod
    def CalcMapUnit(extra_byte):
        if extra_byte > 80 or extra_byte < 1:
            raise ValueError(f"ExtraByte needs to be 1-80: {extra_byte}")
        letter_idx = (extra_byte - 1) % 10
        number_idx = ((extra_byte - 1) - (extra_byte - 1) % 10) / 10 + 1
        return letters[letter_idx] + str(int(number_idx))
    
    def TryReverseHash(self, hash):
        if isinstance(hash, int):
            hash = hex(hash)
        hash = hash.replace("0x", "").lower()
        if hash in self._hashes:
            if self._hashes[hash] != "???":
                return self._hashes[hash]
        self._hashes[hash] = "???"
        return None
    
    def RegisterNewHash(self, flagname):
        hash = "%08x" % mmh3.hash(flagname, signed=False)
        if hash not in self._hashes:
            self._hashes[hash] = flagname
    
    @staticmethod
    def GetSize(datatype, entry):
        size = 8
        if "Array" in datatype:
            size += 4
            if "ArraySize" in entry:
                n = entry["ArraySize"]
            elif "Size" in entry:
                n = entry["Size"]
            elif isinstance(entry["DefaultValue"], list):
                n = len(entry["DefaultValue"])
            else:
                raise ValueError("Could not determine array size")
        else:
            n = 1
        if datatype in ["Bool", "Int", "UInt", "Float", "Enum"]:
            pass
        elif datatype == "BoolArray":
            size += math.ceil((4 if math.ceil(n / 8) < 4 else math.ceil(n / 8)) / 4) * 4
        elif datatype in ["IntArray", "FloatArray", "UIntArray", "EnumArray"]:
            size += n * 4
        elif "Vector2" in datatype:
            size += n * 8
        elif "Vector3" in datatype:
            size += n * 12
        elif "WString16" in datatype:
            size += n * 32
        elif "WString32" in datatype:
            size += n * 64
        elif "WString64" in datatype:
            size += n * 128
        elif "String16" in datatype:
            size += n * 16
        elif "String32" in datatype:
            size += n * 32
        elif "String64" in datatype:
            size += n * 64
        elif "Int64" in datatype or "UInt64" in datatype:
            size += n * 8
        elif datatype == "Bool64bitKey":
            pass
        elif "Binary" in datatype:
            size += n * 4
            size += n * entry["DefaultValue"]
        elif datatype in ["Struct", "BoolExp"]:
            pass
        else:
            raise ValueError(f"Invalid Type: {datatype}")
        return size

    def CalcSize(self, index):
        if self._byml.root_node["MetaData"]["SaveDirectory"][index] != "":
            size = 0x20
            offset = 0x20
            for datatype in valid_types:
                size += 8
                offset += 8
                if datatype == "Bool64bitKey":
                    size += 8
                    offset += 8
                has_keys = False
                if datatype in self._byml.root_node["Data"]:
                    for entry in self._byml.root_node["Data"][datatype]:
                        if entry["SaveFileIndex"] == index:
                            if datatype == "Bool64bitKey":
                                has_keys = True
                            else:
                                offset += 8
                            size += self.GetSize(datatype, entry)
                if has_keys:
                    size += 8
        else:
            size = 0
            offset = 0
        return size, offset
    
    def UpdateMetaData(self):
        sizes = []
        offsets = []
        for i in range(len(self._byml.root_node["MetaData"]["SaveDirectory"])):
            size, offset = self.CalcSize(i)
            sizes.append(size)
            offsets.append(offset)
        size = 0x20
        offset = 0x20
        for datatype in valid_types:
            size += 8
            offset += 8
            if datatype == "Bool64bitKey":
                size += 8
                offset += 8
            has_keys = False
            if datatype in self._byml.root_node["Data"]:
                for entry in self._byml.root_node["Data"][datatype]:
                    if datatype == "Bool64bitKey":
                        has_keys = True
                    else:
                        offset += 8
                    size += self.GetSize(datatype, entry)
            if has_keys:
                size += 8
        self._byml.root_node["MetaData"] = {
            "AllDataSaveOffset": byml.Int(offset),
            "AllDataSaveSize": byml.Int(size),
            "FormatVersion": byml.Int(1),
            "SaveDataOffsetPos": [byml.Int(i) for i in offsets],
            "SaveDataSize": [byml.Int(i) for i in sizes],
            "SaveDirectory": self._byml.root_node["MetaData"]["SaveDirectory"],
            "SaveTypeHash": self._byml.root_node["MetaData"]["SaveTypeHash"]
        }

    @staticmethod
    def ValidateFlag(flag, datatype):
        assert datatype in valid_types, f"Invalid GameData flag type: {datatype}"
        assert isinstance(flag, dict), "Flag entries should be formatted as dictionaries"
        if datatype not in ["Bool64bitKey", "BoolExp"]:
            assert "DefaultValue" in flag, "Flag is missing DefaultValue field"
        assert "Hash" in flag, "Flag is missing Hash field"
        if datatype != "Bool64bitKey":
            flag["Hash"] = byml.UInt(flag["Hash"])
        else:
            flag["Hash"] = byml.ULong(flag["Hash"])
        assert "ResetTypeValue" in flag, "Flag is missing ResetTypeValue field"
        flag["ResetTypeValue"] = byml.Int(flag["ResetTypeValue"])
        if flag["ResetTypeValue"] & (256):
            if "ExtraByte" in flag:
                assert flag["ExtraByte"] >= 1 and flag["ExtraByte"] <= 80, "ExtraByte must be between 1 and 80"
                flag["ExtraByte"] = byml.Int(flag["ExtraByte"])
        assert "SaveFileIndex" in flag, "Flag is missing SaveFileIndex field"
        flag["SaveFileIndex"] = byml.Int(flag["SaveFileIndex"])
        if "Array" in datatype:
            assert "OriginalSize" in flag, "Flag is missing OriginalSize field"
            flag["OriginalSize"] = byml.UInt(flag["OriginalSize"])
            if datatype not in ["EnumArray", "BinaryArray"]:
                assert isinstance(flag["DefaultValue"], list), "DefaultValue for arrays should be a list"
        if datatype == "Bool":
            flag["DefaultValue"] = bool(flag["DefaultValue"])
        elif datatype == "BoolArray":
            flag["DefaultValue"] = [bool(i) for i in flag["DefaultValue"]]
        elif datatype == "Int":
            flag["DefaultValue"] = byml.Int(flag["DefaultValue"])
        elif datatype == "IntArray":
            flag["DefaultValue"] = [byml.Int(i) for i in flag["DefaultValue"]]
        elif datatype == "Float":
            flag["DefaultValue"] = byml.Float(flag["DefaultValue"])
        elif datatype == "FloatArray":
            flag["DefaultValue"] = [byml.Float(i) for i in flag["DefaultValue"]]
        elif datatype == "Enum":
            flag["DefaultValue"] = byml.UInt(flag["DefaultValue"])
            assert "RawValues" in flag, "Enum flag is missing RawValues field"
            assert "Values" in flag, "Enum flag is missing Values field"
            assert len(flag["RawValues"]) == len(flag["Values"]), "Unequal number of RawValues and Values"
            flag["Values"] = [byml.ULong(i) for i in flag["Values"]]
        elif datatype == "EnumArray":
            flag["DefaultValue"] = byml.UInt(flag["DefaultValue"])
            assert "RawValues" in flag, "Enum flag is missing RawValues field"
            assert "Values" in flag, "Enum flag is missing Values field"
            assert len(flag["RawValues"]) == len(flag["Values"]), "Unequal number of RawValues and Values"
            flag["Values"] = [byml.ULong(i) for i in flag["Values"]]
            assert "Size" in flag, "EnumArray flag is missing Size field"
            flag["Size"] = byml.UInt(flag["Size"])
        elif datatype == "Vector2":
            assert isinstance(flag["DefaultValue"], dict), "Vector2 flag DefaultValue should be a dict"
            flag["DefaultValue"] = {"x": byml.Float(flag["DefaultValue"]["x"]),
                                    "y" : byml.Float(flag["DefaultValue"]["y"])}
        elif datatype == "Vector2Array":
            flag["DefaultValue"] = [{"x": byml.Float(i["x"]),
                                    "y" : byml.Float(i["y"])} for i in flag["DefaultValue"]]
        elif datatype == "Vector3":
            assert isinstance(flag["DefaultValue"], dict), "Vector3 flag DefaultValue should be a dict"
            flag["DefaultValue"] = {"x": byml.Float(flag["DefaultValue"]["x"]),
                                    "y" : byml.Float(flag["DefaultValue"]["y"]),
                                    "z" : byml.Float(flag["DefaultValue"]["z"])}
        elif datatype == "Vector3Array":
            flag["DefaultValue"] = [{"x": byml.Float(i["x"]),
                                    "y" : byml.Float(i["y"]),
                                    "z" : byml.Float(i["z"])} for i in flag["DefaultValue"]]
        elif datatype == "String16":
            assert len(flag["DefaultValue"]) < 16, "String16 flag DefaultValue must be under 16 characters"
        elif datatype == "String16Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 16, "String16Array flag DefaultValue values must be under 16 characters"
        elif datatype == "String32":
            assert len(flag["DefaultValue"]) < 32, "String32 flag DefaultValue must be under 32 characters"
        elif datatype == "String32Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 32, "String32Array flag DefaultValue values must be under 32 characters"
        elif datatype == "String64":
            assert len(flag["DefaultValue"]) < 64, "String64 flag DefaultValue must be under 64 characters"
        elif datatype == "String64Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 64, "String64Array flag DefaultValue values must be under 64 characters"
        elif datatype == "Binary":
            flag["DefaultValue"] = byml.UInt(flag["DefaultValue"])
        elif datatype == "BinaryArray":
            flag["DefaultValue"] = byml.UInt(flag["DefaultValue"])
            assert "ArraySize" in flag, "BinaryArray flag is missing ArraySize field"
            flag["ArraySize"] = byml.UInt(flag["ArraySize"])
        elif datatype == "UInt":
            flag["DefaultValue"] = byml.UInt(flag["DefaultValue"])
        elif datatype == "UIntArray":
            flag["DefaultValue"] = [byml.Long(i) for i in flag["DefaultValue"]] # for some reason
        elif datatype == "Int64":
            flag["DefaultValue"] = byml.Long(flag["DefaultValue"])
        elif datatype == "Int64Array":
            flag["DefaultValue"] = [byml.Long(i) for i in flag["DefaultValue"]]
        elif datatype == "UInt64":
            flag["DefaultValue"] = byml.ULong(flag["DefaultValue"])
        elif datatype == "UInt64Array":
            flag["DefaultValue"] = [byml.ULong(i) for i in flag["DefaultValue"]]
        elif datatype == "WString16":
            assert len(flag["DefaultValue"]) < 16, "WString16 flag DefaultValue must be under 16 characters"
        elif datatype == "WString16Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 16, "WString16Array flag DefaultValue values must be under 16 characters"
        elif datatype == "WString32":
            assert len(flag["DefaultValue"]) < 32, "WString32 flag DefaultValue must be under 32 characters"
        elif datatype == "WString32Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 32, "WString32Array flag DefaultValue values must be under 32 characters"
        elif datatype == "WString64":
            assert len(flag["DefaultValue"]) < 64, "WString64 flag DefaultValue must be under 64 characters"
        elif datatype == "WString64Array":
            for string in flag["DefaultValue"]:
                assert len(string) < 64, "WString64Array flag DefaultValue values must be under 64 characters"
        elif datatype == "Struct":
            if "Size" in flag:
                flag["Size"] = byml.UInt(flag["Size"])
            assert isinstance(flag["DefaultValue"], list), "Struct flag DefaultValue should be a list"
            for i, member in enumerate(flag["DefaultValue"]):
                assert "Hash" in member, "Struct member is missing Hash field"
                assert "Value" in member, "Struct member is missing Value field"
                flag["DefaultValue"][i]["Hash"] = byml.UInt(flag["DefaultValue"][i]["Hash"])
                flag["DefaultValue"][i]["Value"] = byml.UInt(flag["DefaultValue"][i]["Value"])
        elif datatype == "BoolExp":
            assert "Values" in flag, "BoolExp flag is missing Values field"
            assert isinstance(flag["Values"], list), "BoolExp Values field should be a list"
            for i, exp in enumerate(flag["Values"]):
                assert isinstance(exp, list), "Individual expressions should be a list"
                assert len(exp) > 0, "Expression does not exist"
                if exp[0] in [0, 1, 2, 10, 11, 12]:
                    assert len(exp) == 2, "Invalid expression length"
                elif exp[0] in [3, 4, 5]:
                    assert len(exp) == 1, "Invalid expression length"
                elif exp[0] in [8, 9, 13, 14]:
                    assert len(exp) == 3, "Invalid expression length"
                else:
                    raise ValueError("Invalid expression")
                for j, op in enumerate(flag["Values"][i]):
                    flag["Values"][i][j] = byml.ULong(op)
        elif datatype == "Bool64bitKey":
            pass
        return flag
    
print(GameData.CalcResetTypeValue("cOnSceneChange", "cOnStartNewData", "cOnSceneInitialize"))