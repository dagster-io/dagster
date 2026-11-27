from pydantic import BaseModel


class DgApiDynamicPartition(BaseModel):
    partitions_def_name: str
    partition_key: str


class DgApiDynamicPartitionsDeleteResult(BaseModel):
    partitions_def_name: str
    partition_keys: list[str]
