# until we figure out whether or not to use extras I am just going to jam everything here
import datetime
import json
import uuid
from typing import List, NamedTuple

from dagster_externals._context import Notification


# TODO: move this into dagster_aws
class S3NotificationWriter:
    def __init__(self, bucket: str, base_key: str, s3_client) -> None:
        self.bucket = bucket
        self.base_key = base_key
        self.s3_client = s3_client
        self.notifs: List[Notification] = []

    def write_notification(self, notif: Notification):
        self.notifs.append(notif)
        if len(self.notifs) > 10:
            self._write_all_notifs()

    def get_next_key(self) -> str:
        monotically_increasing_uuid = uuid.uuid1(0, 0)
        next_file = str(monotically_increasing_uuid) + datetime.datetime.utcnow().strftime(
            "%Y-%m-%d-%H-%M-%S-%f"
        )
        return f"{self.base_key}/{next_file}.json"

    def flush(self) -> None:
        self._write_all_notifs()

    def _write_all_notifs(self) -> None:
        if self.notifs:
            strings_to_write = []
            for notif in self.notifs:
                strings_to_write.append(json.dumps(notif))
            string_to_write = "\n".join(strings_to_write)
            next_key = self.get_next_key()
            self.s3_client.put_object(
                Bucket=self.bucket, Key=next_key, Body=string_to_write.encode("utf-8")
            )
            self.notifs = []


class S3NotificationPage(NamedTuple):
    notifications: List[dict]

class S3NotificationReader:
    def __init__(self, s3_client, bucket: str, base_key: str, page_size: int = 1) -> None:
        self.bucket = bucket
        self.base_key = base_key
        self.s3_client = s3_client
        self.prev_key = None
        self.page_size = page_size

    def get_next_page(self) -> S3NotificationPage:
        list_obj_params = dict(Bucket=self.bucket, Prefix=self.base_key, MaxKeys=self.page_size)
        if self.prev_key:
            list_obj_params['StartAfter'] = self.prev_key
        list_obj_results = self.s3_client.list_objects_v2(**list_obj_params)

        notifs = []

        contents = list_obj_results['Contents']
        for entry in contents:
            key = entry['Key']
            get_obj_response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            muh_bytes = get_obj_response['Body'].read()
            muh_string = muh_bytes.decode()
            jsonlines = muh_string.split("\n")
            for jsonline in jsonlines:
                if jsonline:
                    muh_object = json.loads(jsonline)
                    notifs.append(muh_object)

        return S3NotificationPage(notifications=notifs)