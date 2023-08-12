# from dagster_shell.assets import create_shell_script_asset
#
#
# def test_shell_script_asset():
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     assets_def = create_shell_script_asset(os.path.join(script_dir, "test.sh"), key="foobar")
#     result = materialize(
#         [assets_def],
#         run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
#     )
#     assert result.output_for_node("foobar") == "this is a test message: foobar\n"
#
#
# def test_shell_script_asset_jsonrpc_access():
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     assets_def = create_shell_script_asset(
#         os.path.join(script_dir, "jsonrpc_example.sh"), key="foobar"
#     )
#     result = materialize(
#         [assets_def],
#         run_config={"ops": {"foobar": {"config": {"env": {"MY_ENV_VAR": "foobar"}}}}},
#         tags={"foo": "bar"},
#     )
#     json_result = result.output_for_node("foobar")[1:-1].replace("\\", "")
#     parsed_result = json.loads(json_result)
#     assert parsed_result["result"] == "bar"
#     assert result.output_for_node("foobar")
