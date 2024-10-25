import json
import os

import pandas as pd
from flask import Flask, render_template, request, send_file, session

from core import get_flight, make_ics_from_selected_df_index

app = Flask(__name__)


secret_key = os.urandom(24)
app.secret_key = secret_key


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create_event", methods=["POST"])
def create_ical():
    try:
        flight = request.form.get("flight_number")
        date = request.form.get("flight_date")
        df = get_flight(flight, date)
        # Store the DataFrame as JSON in the session
        session["df"] = df.to_json(orient="split")
        return render_template(
            "select_flight.html", flights=df.to_dict(orient="records")
        )
    except Exception as e:
        error_message = str(e)
        return render_template("index.html", error=error_message)


@app.route("/create_event/<int:index>", methods=["POST"])
def create_ical_from_selected(index):
    # Retrieve the DataFrame from the session and reconstruct it
    df_json = session.get("df")
    if df_json is None:
        return "No flight data found", 400

    df = pd.read_json(df_json, orient="split")
    ics_data = make_ics_from_selected_df_index(df, index)
    flight = df.iloc[index]["flight_number"]

    return send_file(ics_data, as_attachment=True, download_name=f"{flight}.ics")


if __name__ == "__main__":
    app.run()
