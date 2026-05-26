from __future__ import annotations
import hashlib


def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def hash_file(path: str, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class Hasher:
    def __init__(self, algorithm: str = "sha256"):
        self._algorithm = algorithm
        self._hash = hashlib.new(algorithm)

    def update(self, data: bytes) -> None:
        self._hash.update(data)

    def hexdigest(self) -> str:
        return self._hash.hexdigest()

    @property
    def algorithm(self) -> str:
        return self._algorithm
