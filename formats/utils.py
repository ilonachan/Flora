import struct
from abc import ABC, abstractmethod

class ByteReader(ABC):
    @abstractmethod
    def read_bytes(self, len: int) -> bytes:
        pass
    def read_int(self, len: int) -> int:
        return int.from_bytes(self.read_bytes(len), 'little')
    def read_float(self) -> float:
        return struct.unpack('<f', self.read_bytes(4))
    

    @abstractmethod
    def seek(self, loc: int):
        pass
    @property
    @abstractmethod
    def loc(self) -> int:
        pass
    @abstractmethod
    def has_more(self) -> bool:
        pass

class BufferByteReader(ByteReader):
    buffer: bytes
    __loc: int

    def __init__(self, buffer: bytes, loc: int = 0):
        self.buffer = buffer
        self.__loc = loc
    
    def read_bytes(self, len: int) -> bytes:
        data = self.buffer[self.__loc : self.__loc + len]
        self.__loc += len
        return data
    
    @property
    def loc(self) -> int:
        return self.__loc
    @loc.setter
    def loc(self, value):
        self.seek(value)
    def seek(self, loc: int):
        self.__loc = loc
    
    def has_more(self) -> bool:
        return self.loc <= len(self.buffer)

    def __len__(self) -> int:
        return len(self.buffer)
    def __getitem__(self, index) -> bool:
        return self.buffer[index]