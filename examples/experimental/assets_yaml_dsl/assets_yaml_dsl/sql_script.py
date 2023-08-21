import sys


class SomeSqlClient:
    def query(self, query_str: str) -> None:
        sys.stderr.write(f'Querying "{query_str}"\n')


if __name__ == "__main__":
    sql = sys.argv[1]
    client = SomeSqlClient()
    client.query(sql)
