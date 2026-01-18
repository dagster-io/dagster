from datetime import datetime

from airflow import DAG
from airflow.sensors.filesystem import FileSensor

dag = DAG("file_sensor_example", start_date=datetime(2024, 1, 1))

wait_for_file = FileSensor(
    task_id="wait_for_new_customer_files",
    filepath="/path/to/customer_files/*.csv",
    poke_interval=60,  # Check every minute
    timeout=3600,  # Timeout after 1 hour
    mode="poke",
    dag=dag,
)
