import argparse

from rabbitmq.publisher import CSVRecordPublisher

def main():
    parser = argparse.ArgumentParser(prog="publish_sensor_readings")
    parser.add_argument("-T", "--period", type=float, default=None)
    parser.add_argument("-o", "--offset", type=int, default=0)
    parser.add_argument("-n", "--num-records", type=int, default=None)
    args = parser.parse_args()

    publisher = CSVRecordPublisher(
        queue_name="readings",
        filename="data/predictive_maintenance.csv",
        cols=["UDI", "Air temperature [K]", "Process temperature [K]", "Rotational speed [rpm]", "Torque [Nm]"]
    )

    publisher.run(period=args.period, num_records=args.num_records, offset=args.offset)

main()
