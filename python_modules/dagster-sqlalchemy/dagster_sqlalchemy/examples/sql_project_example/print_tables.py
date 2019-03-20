import json

import pandas as pd
import sqlalchemy as sa

from dagster import check

if __name__ == '__main__':
    config_obj = json.load(open('config.json'))
    engine = sa.create_engine(
        'sqlite:///{dbname}.db'.format(dbname=check.str_elem(config_obj, 'dbname'))
    )
    for table in ['num_table', 'sum_table', 'sum_sq_table']:
        table_df = pd.read_sql_table(table, con=engine)
        print(table)
        print(table_df)
