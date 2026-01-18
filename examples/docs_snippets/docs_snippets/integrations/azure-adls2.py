import pandas as pd
from dagster_azure.adls2 import ADLS2Resource, ADLS2SASToken

import dagster as dg


@dg.asset
def example_adls2_asset(adls2: ADLS2Resource):
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": ["A", "B", "C"]})

    csv_data = df.to_csv(index=False)

    file_client = adls2.adls2_client.get_file_client(
        "my-file-system", "path/to/my_dataframe.csv"
    )
    file_client.upload_data(csv_data, overwrite=True)


defs = dg.Definitions(
    assets=[example_adls2_asset],
    resources={
        "adls2": ADLS2Resource(
            storage_account="my_storage_account",
            credential=ADLS2SASToken(token="my_sas_token"),
        )
    },
)
