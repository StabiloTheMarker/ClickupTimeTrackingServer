import logging
import datetime as dt
import requests
import time

logger = logging.getLogger(__name__)


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
        resp = self.session.request(method, path, params)
        try:
            data = resp.json()
        except Exception as e:
            logger.error(
                f"There was an error making request for path {path}: {str(e)}")
            raise Exception(str(e))

    def get_time_entries(self,
                         team_id: str,
                         start_date: dt.datetime = None,
                         end_date: dt.datetime = None,
                         space_id: str = None):
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
            data = self.make_auth_get_request(path, params=params).get("data")
            return data
        except Exception as e:
            logger.error(f"There was an exception getting time_entries for Team id {team_id}: {str(e)}")
            raise Exception(str(e))

