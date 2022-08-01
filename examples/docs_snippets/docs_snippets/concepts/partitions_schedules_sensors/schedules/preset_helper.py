from dagster._legacy import daily_schedule

# start_preset_helper


def daily_schedule_definition_from_pipeline_preset(pipeline, preset_name, start_date):
    preset = pipeline.get_preset(preset_name)
    if not preset:
        raise Exception(
            "Preset {preset_name} was not found "
            "on pipeline {pipeline_name}".format(
                preset_name=preset_name, pipeline_name=pipeline.name
            )
        )

    @daily_schedule(
        start_date=start_date,
        pipeline_name=pipeline.name,
        solid_selection=preset.solid_selection,
        mode=preset.mode,
        tags_fn_for_date=lambda _: preset.tags,
    )
    def my_schedule(_date):
        return preset.run_config

    return my_schedule


# end_preset_helper
