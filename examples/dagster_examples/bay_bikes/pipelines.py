from dagster import ModeDefinition, PresetDefinition, file_relative_path, pipeline

from .resources import local_transporter, mount, production_transporter, temporary_directory_mount
from .solids import (
    consolidate_csv_files,
    download_zipfiles_from_urls,
    unzip_files,
    upload_file_to_bucket,
)

local_mode = ModeDefinition(
    name='local',
    resource_defs={'transporter': local_transporter, 'volume': temporary_directory_mount},
)


production_mode = ModeDefinition(
    name='production', resource_defs={'transporter': production_transporter, 'volume': mount}
)


@pipeline(
    mode_defs=[local_mode, production_mode],
    preset_defs=[
        PresetDefinition.from_files(
            'dev',
            mode='local',
            environment_files=[
                file_relative_path(__file__, 'environments/base.yaml'),
                file_relative_path(__file__, 'environments/dev.yaml'),
            ],
        ),
        PresetDefinition.from_files(
            'production',
            mode='production',
            environment_files=[
                file_relative_path(__file__, 'environments/base.yaml'),
                file_relative_path(__file__, 'environments/production.yaml'),
            ],
        ),
    ],
)
def monthly_bay_bike_etl_pipeline():
    upload_file_to_bucket(consolidate_csv_files(unzip_files(download_zipfiles_from_urls())))
