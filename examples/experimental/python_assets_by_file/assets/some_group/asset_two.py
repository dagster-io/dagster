from dagster_pipes import open_dagster_pipes


class Attrs:
    deps = ["some_group/asset_one"]
    description = "This is asset two."


with open_dagster_pipes() as pipes:
    print("do stuff")
