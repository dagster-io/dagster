import sys

from dagster_external import init_dagster_external


class SomeSqlClient:
    def query(self, query_str: str) -> None:
        sys.stderr.write(f'Querying "{query_str}"\n')


if __name__ == "__main__":
    sql = sys.argv[1]

    context = init_dagster_external()

    client = SomeSqlClient()
    client.query(sql)
    context.report_asset_metadata(context.asset_key, "sql", sql)
    context.log(f"Ran {sql}")
