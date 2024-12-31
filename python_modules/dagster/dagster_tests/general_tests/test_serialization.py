import logging
from asyncio import TimeoutError, gather, wait_for

import pytest
from dagster._serdes.serdes import _WHITELIST_MAP
from dagster._serialization.capnproto.scribe import CapnProtoScribe

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_generate_protobuf_from_class():
    scribe = CapnProtoScribe()
    scribe_tasks = [
        *(
            scribe.from_serializer(serializer)
            for serializer in _WHITELIST_MAP.object_serializers.values()
        ),
        *(
            scribe.from_serializer(serializer)
            for serializer in _WHITELIST_MAP.enum_serializers.values()
        ),
    ]

    try:
        await wait_for(gather(*scribe_tasks), timeout=10)
    except TimeoutError:
        pass

    for type_, willcall in scribe._scribed_types.items():
        if willcall.future.cancelled():
            print(f"{type_} blocking:")
            for waiter in willcall.waiting:
                print("  " + waiter)
