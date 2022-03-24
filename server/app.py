from ast import List
import os
import logging
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
import datetime as dt
from wtforms import Form, BooleanField
from server. clickup_api_client import ClickUpApiClient, TimeEntry
from server.forms import GenerateReportForm

load_dotenv()
logger = logging.getLogger(__name__)

app = Flask(__name__)

TEAM_ID="2618640"

@app.route("/", methods=["GET"])
@app.route("/<start_date>/<end_date>")
def index(start_date = None, end_date=None):
    # The variables Should be ISO format yyyy-mm-dd
    time_entries = None
    if start_date is not None and end_date is not None:
        date_format = r"%Y-%m-%d"
        parsed_start = dt.datetime.strptime(start_date, date_format)
        parsed_end = dt.datetime.strptime(end_date, date_format)
        client = ClickUpApiClient(os.environ.get("BASE_URL"), os.environ.get("TOKEN"))
        time_entries: List[TimeEntry] = client.get_time_entries(TEAM_ID, parsed_start, parsed_end)
    return render_template('index.html', entries=time_entries)


@app.route("/generate-report", methods=["POST"])
def generate_report():
    report_form = GenerateReportForm(request.form)
    start_date = report_form.startdate.data
    end_date = report_form.enddate.data
    list_tasks = report_form.list_tasks.data    
    print(start_date)
    return redirect(url_for('index',start_date=start_date, end_date=end_date))
    