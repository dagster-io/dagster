# start_flat
import dagster as dg


# Assets belong to the `default` group unless `group_name` says otherwise.
@dg.asset(group_name="marketing")
def marketing_summary(): ...


# `group_name` is also available on `AssetSpec`.
campaign_costs = dg.AssetSpec("campaign_costs", group_name="marketing")

# end_flat

# start_nested


# `/` separates the segments of a nested group name. The `marketing` and
# `marketing/paid` parent groups are implied by their children.
@dg.asset(group_name="marketing/paid/search")
def search_spend(): ...


@dg.asset(group_name="marketing/paid/social")
def social_spend(): ...


@dg.asset(group_name="marketing/email")
def email_sends(): ...


# end_nested
