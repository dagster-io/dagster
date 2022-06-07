# pylint: disable=unused-argument
import pytest

from dagster.core.asset_defs.asset_selection import AssetSelection
from dagster.core.asset_defs.decorators import asset


@asset(group_name="ladies")
def alice():
    return "alice"


@asset(group_name="gentlemen")
def bob(alice):
    return "bob"


@asset(group_name="ladies")
def candace(alice):
    return "candace"


@asset(group_name="gentlemen")
def danny(candace):
    return "danny"


@asset(group_name="gentlemen")
def edgar(danny):
    return "edgar"


@asset(group_name="ladies")
def fiona(danny):
    return "fiona"


@asset(group_name="gentlemen")
def george(bob, fiona):
    return "george"


@pytest.fixture
def all_assets():
    return [
        alice,
        bob,
        candace,
        danny,
        edgar,
        fiona,
        george,
    ]


def test_asset_selection_all(all_assets):
    sel = AssetSelection.all()
    assert sel.resolve(all_assets) == all_assets


def test_asset_selection_and(all_assets):
    sel = AssetSelection.keys("alice", "bob") & AssetSelection.keys("bob", "candace")
    assert sel.resolve(all_assets) == {bob}


def test_asset_selection_downstream(all_assets):
    sel_depth_inf = AssetSelection.keys("candace").downstream()
    assert sel_depth_inf.resolve(all_assets) == {candace, danny, edgar, fiona, george}

    sel_depth_1 = AssetSelection.keys("candace").downstream(depth=1)
    assert sel_depth_1.resolve(all_assets) == {candace, danny}


def test_asset_selection_groups(all_assets):
    sel = AssetSelection.groups("ladies")
    assert sel.resolve(all_assets) == {alice, candace, fiona}


def test_asset_selection_keys(all_assets):
    sel = AssetSelection.keys("alice", "bob")
    assert sel.resolve(all_assets) == {alice, bob}


def test_asset_selection_or(all_assets):
    sel = AssetSelection.keys("alice", "bob") | AssetSelection.keys("bob", "candace")
    assert sel.resolve(all_assets) == {alice, bob, candace}


def test_asset_selection_upstream(all_assets):
    sel_depth_inf = AssetSelection.keys("george").upstream()
    assert sel_depth_inf.resolve(all_assets) == {alice, bob, candace, danny, fiona, george}

    sel_depth_1 = AssetSelection.keys("george").upstream(depth=1)
    assert sel_depth_1.resolve(all_assets) == {bob, fiona, george}
