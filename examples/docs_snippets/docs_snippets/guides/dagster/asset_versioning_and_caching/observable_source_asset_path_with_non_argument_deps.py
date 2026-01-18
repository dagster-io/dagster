from hashlib import sha256

import dagster as dg


def sha256_digest_from_str(string: str) -> str:
    hash_sig = sha256()
    hash_sig.update(bytearray(string, "utf8"))
    return hash_sig.hexdigest()


FILE_PATH = dg.file_relative_path(__file__, "input_number.txt")


@dg.observable_source_asset
def input_number():
    with open(FILE_PATH) as ff:
        return dg.DataVersion(sha256_digest_from_str(ff.read()))


@dg.asset(code_version="v6", deps=[input_number])
def versioned_number():
    with open(FILE_PATH) as ff:
        value = int(ff.read())
        return dg.Output(value, data_version=dg.DataVersion(str(value)))


@dg.asset(code_version="v1")
def multiplied_number(versioned_number):
    return versioned_number * 2
