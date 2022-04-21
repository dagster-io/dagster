import concurrent.futures
import tempfile
import time

from user_in_loop.user_in_loop.repo import user_in_the_loop_pipeline

from dagster import execute_pipeline


def run_pipeline(path_to_dir):
    result = execute_pipeline(
        user_in_the_loop_pipeline,
        # start_loop_marker_1
        run_config={
            "solids": {
                "wait_for_condition_met": {"config": {"file_path": f"{path_to_dir}/data.csv"}}
            }
        },
    )
    # end_loop_marker_1
    return result


def create_file(path_to_dir):
    time.sleep(1)
    with open(f"{path_to_dir}/data.csv", "w", encoding="utf8") as fd:
        fd.write("ok")


def test_user_in_loop_pipeline(capsys):
    with tempfile.TemporaryDirectory() as temp_dir:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            f1 = executor.submit(run_pipeline, temp_dir)
            executor.submit(create_file, temp_dir)

            pipeline_run_res = f1.result()
            assert pipeline_run_res.success

    file_path_not_exist = False
    file_path_exist = False
    final_result = False

    captured = capsys.readouterr()
    for line in captured.err.split("\n"):
        if line:
            if "Condition not met" in line:
                file_path_not_exist = True

            if "Condition is met" in line:
                file_path_exist = True

            if "Hello, the computation is completed" in line:
                final_result = True

    assert file_path_not_exist
    assert file_path_exist
    assert final_result
