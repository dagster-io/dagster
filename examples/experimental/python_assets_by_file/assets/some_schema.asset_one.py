from dagster_pipes import open_dagster_pipes


class Attrs:
    description = "This is asset one."


with open_dagster_pipes() as pipes:
    print("do stuff")
