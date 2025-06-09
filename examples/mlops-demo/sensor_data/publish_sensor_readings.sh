#!/bin/bash
wait_for_more() {
  while true; do
    read -p "Type 'more' to publish 500 more readings: " input
    if [[ "$input" == "more" ]]; then
      break
    fi
  done
}

wait_for_more
python publish_sensor_readings.py --num-records 500 --offset 0
wait_for_more
python publish_sensor_readings.py --num-records 500 --offset 500
wait_for_more
python publish_sensor_readings.py --num-records 500 --offset 1000
wait_for_more
python publish_sensor_readings.py --num-records 500 --offset 1500