# GameData

## Overview
**GameData** is a system that uses **flags** to store and save the state of the game at any moment in time. A comprehensive list of all flags is found in `GameDataList.Product.110.byml.zs` (`GameDataList.Product.100.byml.zs` on version 1.0.0) in the `GameData` folder of the romfs. While this file is large and may seem intimidating at first, it becomes significantly easier to manage once you have a basic grasp of how GameData works.

## Flags
Every GameData flag has a few properties, most important of which being their **name** and their **value**. A flag's name is generally a short description of what the flag represents (for example, the flag `PlayerStatus.MasterSwordSleepTimer` represents the time remaining until the Master Sword's energy is restored). A flag's value is, well, its value. What form this value is in depends on the flag's type (see **GameData Types** below). Besides these two properties, a flag also has several others.

#### Other Flag Properties
| Property       | Description                                                                              |
|----------------|------------------------------------------------------------------------------------------|
| DefaultValue   | The flag's default value                                                                 |
| Hash           | A 32-bit murmur3 hash of the flag's name                                                 |
| ResetTypeValue | A bitfield controlling when a flag is reset                                              |
| SaveFileIndex  | The index of the save file where the flag is saved to (-1 when not saved to a save file) |
| OriginalSize   | Property shared by all array types, purpose unknown                                      |

Specific flag types may have additional properties, but those will be discussed when discussing the relevant type.

## GameData Types
There are 35 possible types for GameData flags. 16 of these types represent a raw value, 16 are arrays of values, and 3 are special types.

#### Types
| Typename       | Description/Notes                                                                            |
|----------------|----------------------------------------------------------------------------------------------|
| Bool           | A boolean value (True/False)                                                                 |
| BoolArray      | An array of boolean values                                                                   |
| Int            | A 32-bit signed integer value                                                                |
| IntArray       | An array of 32-bit signed integer values                                                     |
| Float          | A 32-bit floating point value                                                                |
| FloatArray     | An array of 32-bit floating point values                                                     |
| Enum           | A 32-bit murmur3 hash of the name of an enum value - has the additional fields `RawValues` (array of enum value strings) and Values (array of 32-bit murmur3 hashes of the `RawValues`) |
| EnumArray      | An array of 32-bit murmur3 hashes of enum values - has the additional fields `RawValues` (array of enum value strings), `Values` (array of 32-bit murmur3 hashes of the `RawValues`), and `Size` (the size of the array); the `DefaultValue` field instead specifies the default value of each entry in the array |
| Vector2        | A vector composed of two 32-bit floating point values                                        |
| Vector2Array   | An array of vectors composed of two 32-bit floating point values                             |
| Vector3        | A vector composed of three 32-bit floating point values                                      |
| Vector3Array   | An array of vectors composed of three 32-bit floating point values                           |
| String16       | A 16-byte string value                                                                       |
| String16Array  | An array of 16-byte string values                                                            |
| String32       | A 32-byte string value                                                                       |
| String32Array  | An array of 32-byte string values                                                            |
| String64       | A 64-byte string value                                                                       |
| String64Array  | An array of 64-byte string values                                                            |
| Binary         | A binary data blob, the `DefaultValue` specifies the size in bytes                           |
| BinaryArray    | An array of binary data blobs, the `DefaultValue` specifies the size of each entry while `ArraySize` specifies the number of elemnts in the array |
| UInt           | A 32-bit unsigned integer value                                                              |
| UIntArray      | An array of 32-bit unsigned integer values                                                   |
| Int64          | A 64-bit signed integer value                                                                |
| Int64Array     | An array of 64-bit signed integer values                                                     |
| UInt64         | A 64-bit unsigned integer value                                                              |
| UInt64Array    | An array of 64-bit unsigned integer values                                                   |
| WString16      | A 16-byte string value                                                                       |
| WString16Array | An array of 16-byte wide string values                                                       |
| WString32      | A 32-byte wide string value                                                                  |
| WString32Array | An array of 32-byte wide string values                                                       |
| WString64      | A 64-byte wide string value                                                                  |
| WString64Array | An array of 64-byte wide string values                                                       |
| Struct         | An array of member names and their corresponding flag name, groups flags into **structures** for convenient access - has the additional field `Size` (specifies the array size of its members if any are arrays) - see **Struct** below for more |
| BoolExp        | An array of **expressions** that returns a boolean value based on the value of Bool, BoolArray, or other BoolExp flags - see **BoolExp** below for more |
| Bool64bitKey   | A 64-bit key used to represent the state of an actor - note Bool64bitKeys do not have a value or a `DefaultValue` field, their `Hash` field is a 64-bit hash, and they do not have a name - see **Bool64bitKey** below for more |

## Struct
Structs group sets of GameData flags together. For example, the `PlayerStatus` struct groups together a group of flags relevant to the player's current status. Each member flag of a struct has a 

## BoolExp

## Bool64bitKey

## GameDataList

### Reading/Navigating

### Editing