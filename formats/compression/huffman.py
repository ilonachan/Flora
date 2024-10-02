from dataclasses import dataclass
import struct
from typing import Callable, ClassVar, Generic, Optional, Mapping, TypeVar, Union, Tuple

from formats.utils import BufferByteReader, ByteReader


@dataclass(unsafe_hash=True)
class BitInt:
    val: int
    len: int

    ONE: ClassVar["BitInt"]
    ZERO: ClassVar["BitInt"]

    def __init__(self, val: int, len: int):
        self.len = len
        self.val = val & self.mask

    def __len__(self):
        return self.len

    @property
    def mask(self) -> int:
        res = 0
        for _ in range(self.len):
            res <<= 1
            res |= 1
        return res

    def match(self, value: Union[int, "BitInt"]) -> bool:
        if isinstance(value, int):
            return (value ^ self.val) & self.mask == 0
        elif value.len < self.len:
            return False
        return (value.val ^ self.val) & self.mask == 0

    def concat(self, other: "BitInt") -> "BitInt":
        return BitInt(
            (self.val & self.mask) << other.len | (other.val & other.mask),
            self.len + other.len,
        )

    @property
    def msb(self) -> bool:
        if self.len == 0:
            return False
        return self.val & (1 << (self.len - 1)) != 0

    def __format__(self, format_spec: str) -> str:
        trimmed = bin(self.val)[2:][-self.len :]
        trimmed = "0" * max(0, self.len - len(trimmed)) + trimmed
        return "0b" + trimmed

    def __rshift__(self, other: int) -> "BitInt":
        return BitInt(self.val >> other, max(0, self.len - other))

    def __lshift__(self, other: int) -> "BitInt":
        return BitInt(self.val << other, self.len + other)


BitInt.ONE = BitInt(1, 1)
BitInt.ZERO = BitInt(0, 1)

T = TypeVar("T")


class HuffmanNode(Generic[T]):
    __parent: Optional["HuffmanNode[T]"] = None
    __depth: int = 0
    __child0: Optional["HuffmanNode[T]"] = None
    __child1: Optional["HuffmanNode[T]"] = None
    __data: Optional[T] = None

    def __init__(self, parent: Optional["HuffmanNode[T]"] = None):
        self.parent = parent

    @property
    def parent(self) -> Optional["HuffmanNode[T]"]:
        return self.__parent

    @parent.setter
    def parent(self, value):
        self.__parent = value
        self.depth = value.depth + 1 if value is not None else 0

    @property
    def depth(self) -> int:
        return self.__depth

    @depth.setter
    def depth(self, value):
        self.__depth = value
        if self.child0 is not None:
            self.child0.depth = value + 1
        if self.child1 is not None:
            self.child1.depth = value + 1

    @property
    def child0(self) -> Optional["HuffmanNode[T]"]:
        return self.__child0

    @child0.setter
    def child0(self, value):
        self.__child0 = value
        if value is not None:
            if self.data is not None:
                print("WARN: Data nodes are leaf nodes and should not have children")
            value.parent = self

    @property
    def child1(self) -> Optional["HuffmanNode[T]"]:
        return self.__child1

    @child1.setter
    def child1(self, value):
        self.__child1 = value
        if value is not None:
            if self.data is not None:
                print("WARN: Data nodes are leaf nodes and should not have children")
            value.parent = self

    @property
    def data(self) -> Optional[T]:
        return self.__data

    @data.setter
    def data(self, value: T):
        if value is not None and (self.child0 is not None or self.child1 is not None):
            print("WARN: Data nodes are leaf nodes and should not have children")
        self.__data = value

    def to_mapping(self, prefix: BitInt = BitInt(0, 0)) -> Mapping[BitInt, T]:
        if self.data is not None:
            return {prefix: self.data}
        mapping = {}
        if self.child0 is not None:
            mapping |= self.child0.to_mapping(prefix.concat(BitInt.ZERO))
        if self.child1 is not None:
            mapping |= self.child1.to_mapping(prefix.concat(BitInt.ONE))
        return mapping

    def set_at(self, key: BitInt, value: T):
        if key.len == 0:
            self.data = value
            return
        subkey = BitInt(key.val, key.len - 1)
        if key.msb:
            if not self.child1:
                self.child1 = HuffmanNode(self)
            self.child1.set_at(subkey, value)
        else:
            if not self.child0:
                self.child0 = HuffmanNode(self)
            self.child0.set_at(subkey, value)

    def get_at(self, key: BitInt) -> Tuple[T, BitInt]:
        def fetch_dummy():
            raise ValueError()

        return self.get_at_stream(key, fetch_dummy)

    def get_at_stream(
        self, key: BitInt, fetch_more: Callable[[], BitInt]
    ) -> Tuple[T, BitInt]:
        if self.data is not None:
            return (self.data, key)
        if key.len == 0:
            key = key.concat(fetch_more())
        subkey = BitInt(key.val, key.len - 1)
        if key.msb:
            if self.child1 is None:
                raise KeyError()
            return self.child1.get_at_stream(subkey, fetch_more)
        else:
            if self.child0 is None:
                raise KeyError()
            return self.child0.get_at_stream(subkey, fetch_more)

    @classmethod
    def from_mapping(cls, mapping: Mapping[BitInt, T]):
        root = HuffmanNode()
        for k, v in mapping.items():
            root.set_at(k, v)
        return root


def node_from_bytes(
    stream: ByteReader,
    end: int,
    is_data: bool,
    parent: Optional[HuffmanNode[int]] = None,
) -> Optional[HuffmanNode[int]]:
    start = stream.loc

    if start >= end:
        return None
    node = HuffmanNode(parent)
    data = stream[start]
    if is_data:
        node.data = data
        return node

    offset = data & 0x3F
    subzero_start = (start ^ (start & 1)) + offset * 2 + 2
    subzero_isdata = data & 0x80 != 0
    subone_isdata = data & 0x40 != 0

    stream.loc = subzero_start

    node.child0 = node_from_bytes(stream, end, subzero_isdata, node)
    node.child1 = node_from_bytes(stream, end, subone_isdata, node)

    stream.loc = start + 1
    return node


def decompress(data):  # sourcery skip: remove-unreachable-code
    """
    Decompress HUFF-compressed data.
    """

    data = BufferByteReader(data)

    block_size = 8

    magic = data.read_int(1)
    if magic == 0x24:
        block_size = 4
    elif magic == 0x28:
        block_size = 8
    else:
        raise TypeError("This isn't a HUFF-compressed file.")

    dataLen = data.read_int(3)

    treeSize = (data.read_int(1) + 1) * 2
    treeEnd = 4 + treeSize

    out = bytearray(dataLen)
    outPos = 0

    root = node_from_bytes(data, treeEnd, False)
    root: HuffmanNode[int]
    assert root is not None
    
    data.loc = treeEnd
    
    nibble = None

    window = BitInt(0, 0)
    while outPos < dataLen:

        def read_next_window():
            val = BitInt(data.read_int(4), 32)
            return val

        byte, window = root.get_at_stream(window, read_next_window)

        if block_size == 4:
            if nibble is None:
                nibble = byte << 4
            else:
                nibble |= byte
                out[outPos] = nibble
                outPos += 1
                nibble = None
        else:
            out[outPos] = byte
            outPos += 1

    raise NotImplementedError("huffman decompression")

    return bytes(out)
