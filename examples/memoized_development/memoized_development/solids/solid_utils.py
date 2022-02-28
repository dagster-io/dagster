import hashlib


def get_hash_for_file(path):
    h = hashlib.new("md5")
    with open(path, "rb", encoding="utf8") as f:
        data = f.read()
    h.update(data)
    digest = h.hexdigest()
    return digest
