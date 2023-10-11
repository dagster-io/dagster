# dagster_pipes has no dependencies
from dagster_pipes import open_dagster_pipes, PipesContext

def main(pipes: PipesContext):
    # built-in parameter passing, not CLI apps
    input_data = load_dataframe(pipes.partition_key)
    transformed_data = transform_dataframe(input_data)
    save_dataframe(transformed_data)
    nrows = len(transformed_data)
    pipes.report_asset_materialization(metadata={"nrows": nrows}) 
    all_not_null = bool(transformed_data["trace_id"].notnull().all())
    pipes.report_asset_check("trace_id_not_null", passed=all_not_null)

if __name__ == "__main__":
    with open_dagster_pipes() as pipes:
        main(pipes)