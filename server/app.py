from ast import List
import os
import logging
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
import datetime as dt
import pandas as pd
from wtforms import Form, BooleanField
from server. clickup_api_client import ClickUpApiClient, TimeEntry
from server.forms import GenerateReportForm

load_dotenv()
logger = logging.getLogger(__name__)
date_format = r"%Y-%m-%d"

app = Flask(__name__)

TEAM_ID="2618640"

def get_work_hours_df_from_start_date_and_end_date(start_date: str, end_date: str) -> pd.DataFrame:
    parsed_start = dt.datetime.strptime(start_date, date_format)
    parsed_end = dt.datetime.strptime(end_date, date_format)
    client = ClickUpApiClient(os.environ.get("BASE_URL"), os.environ.get("TOKEN"))
    work_time_df = client.get_hours_worked_per_day_for_month(parsed_start, parsed_end, ["Kyndril", "AiTrader", "Felder Group"])
    return work_time_df

@app.route("/", methods=["GET"])
@app.route("/<start_date>/<end_date>")
def index(start_date = None, end_date=None):
    # The variables Should be ISO format yyyy-mm-dd
    work_time_df = None
    if start_date is not None and end_date is not None:
       work_time_df = get_work_hours_df_from_start_date_and_end_date(start_date, end_date)
    return render_template('index.html', data=work_time_df)

@app.route("/table_only/<start_date>/<end_date>", methods=["GET"])
def table_only_view(start_date, end_date):
    work_time_df = None
    if start_date is not None and end_date is not None:
       work_time_df = get_work_hours_df_from_start_date_and_end_date(start_date, end_date)
    return render_template('table_only.html', data=work_time_df)

@app.route("/generate-report", methods=["POST"])
def generate_report():
    report_form = GenerateReportForm(request.form)
    start_date = report_form.startdate.data
    end_date = report_form.enddate.data
    list_tasks = report_form.list_tasks.data    
    return redirect(url_for('index',start_date=str(start_date), end_date=str(end_date)))
    