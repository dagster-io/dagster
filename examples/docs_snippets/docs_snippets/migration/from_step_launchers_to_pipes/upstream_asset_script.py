import boto3
from dagster_pipes import PipesS3MessageWriter, open_dagster_pipes

from my_lib import get_data_frame  # type: ignore


def main():
    with open_dagster_pipes(
        message_writer=PipesS3MessageWriter(client=boto3.client("s3")),
    ) as pipes:
        df = get_data_frame()

        # change according to your needs
        path = "s3://" + "<my-bucket>/" + pipes.asset_key + "/.parquet"

        # this was probably previously logged by the IOManager
        pipes.add_output_metadata({"path": path})

        df.write.parquet(path)


if __name__ == "__main__":
    main()
