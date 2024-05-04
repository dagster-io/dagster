from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    print("do stuff")
