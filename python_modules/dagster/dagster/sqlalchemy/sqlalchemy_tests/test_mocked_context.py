import sqlalchemy
import dagster.sqlalchemy as dagster_sa


# disable warnings about malformed inheritance
# pylint: disable=W0221, W0223
class MockEngine(sqlalchemy.engine.Engine):
    def __init__(self):
        super(MockEngine, self).__init__(None, None, None)

    def connect(self):
        raise Exception('should not call')

    def raw_connection(self):
        raise Exception('should not call')


def test_mock():
    sa_resource = dagster_sa.SqlAlchemyResource(engine=MockEngine(), mock_sql=True)
    context = dagster_sa.common.create_sql_alchemy_context_from_sa_resource(sa_resource)
    dagster_sa.common.execute_sql_text_on_context(context, 'NOPE')
