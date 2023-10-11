import sys


def main():
    # user has to write bespoke CLI app
    assert sys.argv[1] == "--execution-date"
    execution_date = sys.argv[2]
    input_data = load_dataframe(execution_date)
    transformed_data = transform_dataframe(input_data)
    save_dataframe(transformed_data)
    len(transformed_data)
    all_not_null = bool(transformed_data["trace_id"].notnull().all())
    # manually write to file so xcom can pick it up
    with open("/airflow/xcom/return.json", "w") as f:
        f.write(json.dumps({"metadata": {"nrows": execution_date}}) + "\n")
        f.write(json.dumps({"check": {"name": "trace_id_not_null", "passed": all_not_null}}) + "\n")


if __name__ == "__main__":
    main()
