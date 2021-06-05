# Re-execution: Starting with the download_data solid and all its descendents
reexecution_result_specific_selection = reexecute_pipeline(
    unreliable_pipeline,
    parent_run_id=pipeline_result_full.run_id,
    run_config=run_config,
    instance=instance,
    solid_selection=['unreliable+*']
)
