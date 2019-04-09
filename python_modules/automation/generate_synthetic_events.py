import datetime
import functools
import json
import os
import random
import secrets
import tempfile
import uuid

import boto3
import click

from multiprocessing import Pool

from faker import Faker
from faker.providers import internet

from random_useragent.random_useragent import Randomize

# Number of processes to use for multiprocessing dates
NUM_PROCESSES = 4


class EventGenerator:
    '''Generates a set of synthetic behavioral events, with timestamps constrained to a particular date.
    '''

    def __init__(self, start_date):
        self.faker = Faker()
        self.faker.add_provider(internet)
        self.start_date = start_date
        self.ua_generator = Randomize()

    def _gen_user_agent(self):
        devices = [
            ('desktop', 'mac'),
            ('desktop', 'windows'),
            ('tablet', 'ios'),
            ('smartphone', 'ios'),
            ('smartphone', 'android'),
        ]
        ua = self.ua_generator.random_agent(*random.choice(devices))
        return ua

    def _gen_event_type(self):
        '''Creates event type like "io.dagster.page_view".
        '''
        event_types = [
            'page_view',
            'button_click',
            'reload',
            'user_create',
            'user_delete',
            'signup',
        ]
        return 'io.dagster.{}'.format(random.choice(event_types))

    def _gen_timestamp(self):
        midnight = datetime.datetime.combine(
            self.start_date, datetime.time.min, tzinfo=datetime.timezone.utc
        ).timestamp()
        return midnight + random.randint(0, 86400 - 1)

    def __iter__(self):
        return self

    def __next__(self):
        # pylint: disable=no-member
        return json.dumps(
            {
                'environment': 'production',
                'method': 'GET',
                # Nested dicts
                'cookies': {
                    'session': secrets.token_urlsafe(16),
                    'persistent': secrets.token_urlsafe(16),
                },
                'run_id': self.faker.uuid4(),
                'type': self._gen_event_type(),
                'user_agent': self._gen_user_agent(),
                'ip_address': self.faker.ipv4_public(),
                'timestamp': self._gen_timestamp(),
                'url': '/' + self.faker.uri_path(),
                # like any good production system, we throw some random PII in our behavioral events
                'name': self.faker.name(),
                'email': self.faker.ascii_email(),
                # Nested lists
                'location': list(self.faker.location_on_land(coords_only=False)),
            }
        )


def create_events_file_for_date(date, num_events_per_file):
    eg = EventGenerator(date)

    f = tempfile.NamedTemporaryFile(delete=False)
    for _ in range(num_events_per_file):
        f.write(str.encode(next(eg) + '\n'))
    f.close()
    return f.name


def write_to_s3(filename_and_date, s3_bucket, s3_prefix, num_files):
    filename, date = filename_and_date
    s3_client = boto3.client('s3')
    for _ in range(num_files):
        s3_path = os.path.join(
            s3_prefix, datetime.datetime.strftime(date, "%Y/%m/%d"), 'json-' + uuid.uuid4().hex
        )
        print("Writing events file to S3 path: %s" % s3_path)
        s3_client.put_object(Body=open(filename, 'rb'), Bucket=s3_bucket, Key=s3_path)


@click.command()
@click.option('--s3-bucket', help='The S3 bucket to use', required=True)
@click.option('--s3-prefix', help='The S3 prefix to use', required=True)
@click.option(
    '--start-date',
    help='The starting UTC date (in format 2019-01-01) for which to generate events.',
    required=True,
)
@click.option(
    '--end-date',
    help='The ending UTC date, exclusive (in format 2019-01-01) for which to generate events.',
    required=True,
)
@click.option('--num-files', default=100, help='Total number of event files.', required=True)
@click.option(
    '--num-events-per-file',
    default=100000,
    help='Batch size, number of events per file.',
    required=True,
)
@click.option('--dry-run', is_flag=True, help='Dry runs won\'t write to S3.')
def run(s3_bucket, s3_prefix, start_date, end_date, num_files, num_events_per_file, dry_run):
    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    dates = [start + datetime.timedelta(days=x) for x in range(0, (end - start).days)]

    # Synthesize date files first
    with Pool(processes=NUM_PROCESSES) as p:
        event_files = p.map(
            functools.partial(create_events_file_for_date, num_events_per_file=num_events_per_file),
            dates,
        )

    if not dry_run:
        with Pool(processes=NUM_PROCESSES) as p:
            p.map(
                functools.partial(
                    write_to_s3, s3_bucket=s3_bucket, s3_prefix=s3_prefix, num_files=num_files
                ),
                zip(event_files, dates),
            )

        for f in event_files:
            os.unlink(f)


if __name__ == "__main__":
    run()  # pylint:disable=E1120
