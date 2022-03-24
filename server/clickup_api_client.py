from __future__ import annotations
from ast import Dict, List
from dataclasses import dataclass
import logging
import datetime as dt
import requests
import time

logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    name: str


@dataclass
class TimeEntry:
    id: str
    start: dt.datetime
    end: dt.datetime
    duration: dt.timedelta
    task: Task
    at: dt.datetime
    list_name: str
    folder_name: str
    space_name: str
    tags: List[str]

    @staticmethod
    def from_dict(d: Dict) -> TimeEntry:
        task = Task(id=d.get("task").get("id"), name=d.get("task").get("name"))
        start = transform_unix_ms_into_datetime(int(d.get("start")))
        end = transform_unix_ms_into_datetime(int(d.get("end")))
        at = transform_unix_ms_into_datetime(int(d.get("at")))
        duration = transform_unix_ms_duration_into_hours(int(d.get("duration")))
        input = {
            'id': d.get("id"),
            'start': start,
            'end': end,
            'at': at,
            'list_name': d.get("task_location").get("list_name"),
            'folder_name': d.get("task_location").get("folder_name"),
            'space_name': d.get("task_location").get("space_name"),
            'tags': [x.get("name") for x in d.get("task_tags")] if d.get("task_tags") is not None else None,
            'task': task,
            'duration': duration
        }
        entry = TimeEntry(**input)
        return entry


def transform_unix_ms_duration_into_hours(dur: int) -> float:
    return float(dur / 1000 / 60 / 60)


def transform_unix_ms_into_datetime(unix_time: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(int(unix_time/1000))


class ClickUpApiClient:

    def __init__(self, base_url: str, token: str) -> None:
        self.token = token
        self.headers = {"Authorization": token}
        self.session = requests.Session()
        self.base_url = base_url
        if self.base_url[-1] != "/":
            self.base_url += "/"

    def make_auth_request(self, path, method="GET", params=None):
        if path[0] == "/":
            path = path[1:]
        resp: requests.Response = self.session.request(
            method, headers=self.headers, url=self.base_url + path, params=params)
        if resp.status_code != 200:
            raise Exception(
                f"Something went wrong. Resp status-code: {resp.status_code}")
        try:
            data = resp.json()
            return data
        except Exception as e:
            logger.error(
                f"There was an error making request for path {path}: {str(e)}")
            raise Exception(str(e))

    def get_time_entries(self,
                         team_id: str,
                         start_date: dt.datetime = None,
                         end_date: dt.datetime = None,
                         space_id: str = None) -> List[TimeEntry]:
        unix_start = None
        unix_end = None
        if start_date is not None and end_date is not None:
            unix_start = int(time.mktime(start_date.timetuple())) * 1000
            unix_end = int(time.mktime(end_date.timetuple())) * 1000
        path = f"team/{team_id}/time_entries"
        params = {"include_location_names": "true",
                  "start_date": unix_start,
                  "end_date": unix_end,
                  "space_id": space_id}
        try:
            data = self.make_auth_request(path, params=params).get("data")
            return [TimeEntry.from_dict(x) for x in data]
        except Exception as e:
            logger.error(
                f"There was an exception getting time_entries for Team id {team_id}: {str(e)}")
            raise Exception(str(e))
