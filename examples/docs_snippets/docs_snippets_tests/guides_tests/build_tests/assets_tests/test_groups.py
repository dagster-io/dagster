from dagster import load_assets_from_modules


def test_groups():
    from docs_snippets.guides.build.assets.metadata import groups

    group_names = {
        key.to_user_string(): group_name
        for asset in load_assets_from_modules([groups])
        for key, group_name in asset.group_names_by_key.items()
    }
    assert group_names == {
        "marketing_summary": "marketing",
        "search_spend": "marketing/paid/search",
        "social_spend": "marketing/paid/social",
        "email_sends": "marketing/email",
    }
    assert groups.campaign_costs.group_name == "marketing"
