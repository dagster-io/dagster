import dateutil.parser


def convert_airflow_datestr_to_epoch_ts(airflow_ts):
    '''convert_airflow_datestr_to_epoch_ts
    Converts Airflow time strings (e.g. 2019-06-26T17:19:09+00:00) to epoch timestamps.
    '''
    dt = dateutil.parser.parse(airflow_ts)
    return (dt - dateutil.parser.parse('1970-01-01T00:00:00+00:00')).total_seconds()
