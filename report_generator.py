import math
import os
import datetime as dt
from calendar import monthrange
import logging
from pprint import pprint
import matplotlib.pyplot as plt
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from matplotlib.backends.backend_pdf import PdfPages

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

    def get_time_entries(team_id: str,
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
            data = make_auth_get_request(path, params=params).get("data")
            return data
        except Exception as e:
            logger.error(f"There was an exception getting time_entries for Team id {team_id}: {str(e)}")
            raise Exception(str(e))


TEAM_ID = "2618640"
BASE_URL = "https://api.clickup.com/api/v2/"
TOKEN = os.environ.get("TOKEN")
LIST_NAMES = ["Kyndril", "AiTrader", "Felder Group"]
TOKEN = "pk_4540798_7DP9OI7XQYMSSDWPXE3FFP7OIQI4M5SP"


def make_auth_get_request(path, params=None):
    headers = {"Authorization": TOKEN}
    resp = requests.get(BASE_URL + path, headers=headers, params=params).json()
    return resp


def get_spaces():
    path = f"team/{TEAM_ID}/space?archived=false"
    return make_auth_get_request(path).get("spaces")


def get_folders(space_id: str):
    path = f"space/{space_id}/folder"
    return make_auth_get_request(path)


def get_folderless_lists(space_id: str):
    path = f"space/{space_id}/list?archived=false"
    return make_auth_get_request(path).get("lists")


def get_lists(folder_id: str):
    path = f"folder/{folder_id}/list?archived=false"
    return make_auth_get_request(path).get("lists")


def get_tasks(list_id: str):
    path = f"list/{list_id}/task?archived=false"
    return make_auth_get_request(path).get("tasks")


def get_task(task_id: str):
    path = f"task/{task_id}"
    return make_auth_get_request(path)


def get_all_workspace_tasks():
    spaces = get_spaces()
    tasks = []
    for space in spaces:
        lists = get_folderless_lists(space.get("id"))
        for list in lists:
            t = get_tasks(list.get("id"))
            tasks += t
    return tasks


def get_time_entries(team_id: str,
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
    return make_auth_get_request(path, params=params).get("data")


def transform_unix_ms_duration_into_hours(dur: int) -> float:
    return float(dur / 1000 / 60 / 60)


def transform_unix_ms_into_datetime(unix_time: int) -> dt.date:
    return dt.datetime.fromtimestamp(int(unix_time/1000))


if __name__ == "__main__":
    entries = get_time_entries(TEAM_ID)
    date_index = []
    row_entries = []
    for entry in entries:
        list_name = entry.get("task_location").get("list_name")
        at = transform_unix_ms_into_datetime(int(entry.get("end")))
        duration = round(transform_unix_ms_duration_into_hours(
            int(entry.get("duration"))), 2)
        if list_name in LIST_NAMES:
            date_index.append(at.date())
            list_index = LIST_NAMES.index(list_name)
            temp_row = [0 for _ in LIST_NAMES]
            temp_row[list_index] = duration
            row_entries.append(temp_row)
    df = pd.DataFrame(data=row_entries)
    df = pd.concat([df, pd.Series(date_index)], axis=1)
    df.columns = LIST_NAMES + ["date"]
    df = df.groupby(by="date").sum()
    temp_index = df.index
    df = df.apply(lambda series: pd.Series([math.ceil(x) for x in series]))
    df.index = temp_index

    # Fill out the rest of the month with zeros
    merge_index = [str(dt.date(2022, 3, d))
                   for d in range(1, monthrange(2022, 3)[1] + 1)]
    for i in merge_index:
        if i not in [str(x) for x in df.index]:
            temp_df = pd.DataFrame(
                data=[[0]*len(LIST_NAMES)], index=[i], columns=LIST_NAMES)
            df = pd.concat([df, temp_df], axis=0)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # zero_df = pd.DataFrame(data=[[0]*len(LIST_NAMES)]*len(merge_index), index=merge_index)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(
        cellText=df.values, colLabels=df.columns, rowLabels=df.index, loc='center')
    pp = PdfPages("Timetracking.pdf")
    pp.savefig(fig, bbox_inches='tight')
    pp.close()
