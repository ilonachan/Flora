import os
import contextlib

from .huffman import decompress as huffman_decompress

def test_file(filename: str, base: str):
    with open(os.path.join(base, filename), "rb") as f:
        data = f.read()
    with contextlib.suppress(TypeError):
        huffman_decompress(data[4:])
        
def test_all(base: str):
    for root, dirs, files in os.walk(os.path.join(base, "data/bg_failed")):
        for filename in files:
            if filename.endswith(".arc"):
                path = os.path.relpath(os.path.join(root, filename), base)
                test_file(path, base)

if __name__ == "__main__":
    test_all("./data/game_root/lt1_eu/")