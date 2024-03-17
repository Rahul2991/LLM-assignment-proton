import os
import hashlib

def get_file_size(file_path):
    size_kb = os.path.getsize(file_path) / 1024
    return size_kb

def get_file_hash(file_path):
    # Example: SHA-256
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()