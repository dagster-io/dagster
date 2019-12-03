from dagster import pipeline
from dagster.utils import file_relative_path

from .solids import download_and_validate_json

# add alert on schema failures

# schedule this every 5 minutes
# schedule this every 30 seconds
# # --- 2nd pipeline is for inserting json data into DB


@pipeline
def download_gbfs_files():
    download_and_validate_json(
        file_relative_path(__file__, 'schema/gbfs.json'),
        'https://gbfs.baywheels.com/gbfs/gbfs.json',
        name='download_and_validate_gbfs',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/system_alerts.json'),
        'https://gbfs.baywheels.com/gbfs/en/system_alerts.json',
        name='download_and_validate_system_alerts',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/system_regions.json'),
        'https://gbfs.baywheels.com/gbfs/en/system_regions.json',
        name='download_and_validate_system_regions',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/system_calendar.json'),
        'https://gbfs.baywheels.com/gbfs/en/system_calendar.json',
        name='download_and_validate_system_calendar',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/system_hours.json'),
        'https://gbfs.baywheels.com/gbfs/en/system_hours.json',
        name='download_and_validate_system_hours',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/free_bike_status.json'),
        'https://gbfs.baywheels.com/gbfs/en/free_bike_status.json',
        name='download_and_validate_free_bike_status',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/station_status.json'),
        'https://gbfs.baywheels.com/gbfs/en/station_status.json',
        name='download_and_validate_station_status',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/station_information.json'),
        'https://gbfs.baywheels.com/gbfs/en/station_information.json',
        name='download_and_validate_station_information',
    )()
    download_and_validate_json(
        file_relative_path(__file__, 'schema/system_information.json'),
        'https://gbfs.baywheels.com/gbfs/en/system_information.json',
        name='download_and_validate_system_information',
    )()
