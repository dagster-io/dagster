from hashlib import sha256

from dagster import LogicalVersion, asset, file_relative_path, observable_source_asset


def sha256_digest_from_str(string: str) -> str:
    hash_sig = sha256()
    hash_sig.update(bytearray(string, "utf8"))
    return hash_sig.hexdigest()


FILE_PATH = file_relative_path(__file__, "input_number.txt")


@observable_source_asset
def input_number():
    with open(FILE_PATH) as ff:
        return LogicalVersion(sha256_digest_from_str(ff.read()))


@asset(code_version="v3", non_argument_deps={"input_number"})
def versioned_number():
    with open(FILE_PATH) as ff:
        return int(ff.read())


@asset(code_version="v1")
def multipled_number(versioned_number):
    return versioned_number * 2
