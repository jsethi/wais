from __future__ import annotations

from core.hashing.utils import hash_bytes, hash_file, Hasher


class TestHashing:
    def test_hash_bytes_sha256(self):
        result = hash_bytes(b"hello world", "sha256")
        assert len(result) == 64
        assert result == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_hash_bytes_md5(self):
        result = hash_bytes(b"hello world", "md5")
        assert len(result) == 32
        assert result == "5eb63bbbe01eeed093cb22bb8f5acdc3"

    def test_hash_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello world")
        result = hash_file(str(f), "sha256")
        assert len(result) == 64

    def test_hasher_class(self):
        h = Hasher("sha256")
        h.update(b"hello ")
        h.update(b"world")
        assert h.hexdigest() == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert h.algorithm == "sha256"
