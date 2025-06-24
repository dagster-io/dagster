import dagster as dg


class Engine:
    def execute(self, query: str): ...


def get_engine(connection_url: str) -> Engine:
    return Engine()


class MyDatabaseResource(dg.ConfigurableResource):
    connection_url: str

    def query(self, query: str):
        return get_engine(self.connection_url).execute(query)


@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(
        resources={
            # To send a query to the database, you can call my_db_resource.query("QUERY HERE")
            # in the asset, op, or job where you reference my_db_resource
            "my_db_resource": MyDatabaseResource(connection_url="")
        }
    )
