import logging
from asyncio import TimeoutError, gather, wait_for
from collections.abc import Mapping
from typing import ForwardRef, Union

import pytest
from dagster._serdes.serdes import _WHITELIST_MAP
from dagster._serialization.base.types import normalize_type
from dagster._serialization.capnproto.scribe import CapnProtoScribe
from dagster._serialization.capnproto.compile import CapnProtoCompiler

logger = logging.getLogger(__name__)


def _find_serializer_for_type(type_name: str):
    for serializer in _WHITELIST_MAP.object_serializers.values():
        if serializer.klass.__name__ == type_name:
            return serializer
    for serializer in _WHITELIST_MAP.enum_serializers.values():
        if serializer.klass.__name__ == type_name:
            return serializer
    raise ValueError(f"Could not find serializer for type {type_name}")


@pytest.mark.asyncio
async def test_compile_all():
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
        for type_, willcall in scribe.get_will_call():
            if willcall.future.cancelled():
                print(f"{type_} blocking:")
                for waiter in willcall.waiting:
                    print("  " + waiter)
        raise

    compiler = CapnProtoCompiler()
    
    for type_, willcall in scribe.get_will_call():
        async for part in compiler.compile_message(willcall.future.result()):
            for line in part.render():
                print(line)
        


@pytest.mark.asyncio
async def test_circular_types():
    scribe = CapnProtoScribe()
    await scribe.from_serializer(_find_serializer_for_type("DefaultSensorStatus"))
    await scribe.from_serializer(_find_serializer_for_type("SensorType"))
    try:
        await wait_for(scribe.from_serializer(_find_serializer_for_type("SensorSnap")), timeout=10)  # type: ignore
    except TimeoutError:
        pass

    for type_, willcall in scribe.get_will_call():
        if willcall.future.cancelled():
            print(f"{type_} blocking:")
            for waiter in willcall.waiting:
                print("  " + waiter)


@pytest.mark.asyncio
async def test_detect_recursive_type():
    normalized_single_level_recursive_type = normalize_type(
        Union[
            int,
            str,
            bool,
            float,
            Mapping[
                str,
                Union[
                    int,
                    str,
                    bool,
                    float,
                    Mapping[
                        str,
                        Union[
                            int,
                            str,
                            bool,
                            float,
                            Mapping[str, Union[int, str, bool, float, Mapping]],
                        ],
                    ],
                ],
            ],
        ]
    )
    assert (
        normalized_single_level_recursive_type
        == Union[int, str, bool, float, Mapping[str, ForwardRef("self")]]
    )

    normalized_multi_level_recursive_type = normalize_type(
        Union[
            int,
            Mapping[
                str,
                Union[
                    int,
                    Mapping[
                        int,
                        Union[
                            int,
                            Mapping[
                                str,
                                Union[
                                    int, Mapping[int, Union[int, Mapping[str, Union[int, Mapping]]]]
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ]
    )
    assert (
        normalized_multi_level_recursive_type
        == Union[int, Mapping[str, Union[int, Mapping[int, ForwardRef("self")]]]]
    )

    def create_recursive_double_type(n: int) -> type:
        if n == 0:
            return Mapping
        return Mapping[
            int,
            Union[
                str,
                Mapping[str, create_recursive_double_type(n - 1)],
                create_recursive_double_type(n - 1),
            ],
        ]

    double_reference = normalize_type(create_recursive_double_type(4))
    assert (
        double_reference
        == Mapping[int, Union[str, Mapping[str, ForwardRef("self")], ForwardRef("self")]]
    )
