# until we figure out whether or not to use extras I am just going to jam everything here
import datetime
import json
import uuid
from typing import List

from dagster_externals._context import Notification


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
