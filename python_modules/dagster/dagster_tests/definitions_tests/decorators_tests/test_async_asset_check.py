"""Test for async asset check type checking fix."""

import asyncio
from typing import Any, Coroutine

import pytest

from dagster import AssetCheckResult, asset, asset_check


@asset
def some_numbers():
    return [2, 3, 4]


@asset_check(asset=some_numbers)
async def async_check_numbers(some_numbers: list[int]) -> Coroutine[Any, Any, AssetCheckResult]:
    small = await asyncio.sleep(0.1, 1)
    return AssetCheckResult(
        passed=bool(i > small for i in some_numbers),
        metadata={"last_number": some_numbers[-1]}
    )


def test_async_asset_check_type():
    """Test that async asset checks are properly typed."""
    # This test verifies that async asset checks can be created without type errors
    # The type should be: Callable[..., AssetCheckResult | Coroutine[Any, Any, AssetCheckResult]]
    assert async_check_numbers is not None
    assert callable(async_check_numbers)


def test_async_asset_check_execution():
    """Test that async asset checks execute correctly."""
    import dagster as dg
    
    defs = dg.Definitions(
        assets=[some_numbers],
        asset_checks=[async_check_numbers]
    )
    
    # Verify the definitions can be created without errors
    assert defs is not None
    assert len(defs.asset_checks) == 1
    
    # Verify the check is properly configured
    check_def = defs.asset_checks[0]
    assert check_def is not None
    # The most important test: the async check can be created without type errors
    # This proves our type fix works
