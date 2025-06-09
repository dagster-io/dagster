import argparse

from rabbitmq.publisher import CSVRecordPublisher

def main():
    parser = argparse.ArgumentParser(prog="publish_machine_statuses")
    parser.add_argument("-T", "--period", type=float, default=None)
    parser.add_argument("-o", "--offset", type=int, default=0)
    parser.add_argument("-n", "--num-records", type=int, default=None)
    args = parser.parse_args()

    publisher = CSVRecordPublisher(
        queue_name="daily_statuses",
        filename="data/predictive_maintenance.csv",
        cols=["UDI", "Target"]
    )

    publisher.run(period=args.period, num_records=args.num_records, offset=args.offset)

main()

