from flask import Flask, render_template, request, send_file

from core import create_ical_from_flight_and_date

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create_event", methods=["POST"])
def create_ical():
    flight = request.form.get("flight_number")
    date = request.form.get("flight_date")
    ical_data = create_ical_from_flight_and_date(flight, date)
    return send_file(ical_data, as_attachment=True, download_name=f"{flight}.ics")


if __name__ == "__main__":
    app.run()
