import sys

from dagster_pipes import open_dagster_pipes


class SomeSqlClient:
    def query(self, query_str: str) -> None:
        sys.stderr.write(f'Querying "{query_str}"\n')


if __name__ == "__main__":
    sql = sys.argv[1]

    with open_dagster_pipes() as pipes:
        client = SomeSqlClient()
        client.query(sql)
        pipes.report_asset_materialization(metadata={"sql": sql})
        pipes.log.info(f"Ran {sql}")
