import io
from datetime import datetime

import icalendar
from pyflightdata import FlightData
from pytz import timezone

f = FlightData()


def create_ical_from_flight_and_date(flight_number: str, date: str):
    date = parse_date(date)
    flight_number = parse_flight_number(flight_number)
    flight_info = get_flight_for_date(flight_number, date)
    if not flight_info:
        raise ValueError(
            "No flight information found for the given flight number and date."
        )
    parsed_info = parse_flight_info(flight_info)
    ical_event = make_ical_event(parsed_info)
    ical_bytes = io.BytesIO(ical_event)
    return ical_bytes


def parse_date(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d")


def parse_flight_number(flight_number: str) -> str:
    return ''.join(filter(str.isalnum, flight_number.upper()))


def get_flight_for_date(flight_number: str, date: str) -> dict:
    flight_info = f.get_flight_for_date(flight_number, date)
    print(flight_info)
    return flight_info


def parse_flight_info(flight_info: dict) -> dict:
    flight_number = flight_info[0]["identification"]["number"]["default"]
    scheduled_departure = (
        flight_info[0]["time"]["scheduled"]["departure_date"]
        + " "
        + flight_info[0]["time"]["scheduled"]["departure_time"]
    )
    scheduled_arrival = (
        flight_info[0]["time"]["scheduled"]["arrival_date"]
        + " "
        + flight_info[0]["time"]["scheduled"]["arrival_time"]
    )
    airline_name = flight_info[0]["airline"]["name"]
    origin_airport = flight_info[0]["airport"]["origin"]["name"]
    destination_airport = flight_info[0]["airport"]["destination"]["name"]
    origin_timezone = flight_info[0]["airport"]["origin"]["timezone"]["name"]
    destination_timezone = flight_info[0]["airport"]["destination"]["timezone"]["name"]
    origin_airport_code = flight_info[0]["airport"]["origin"]["code"]["iata"]
    destination_airport_code = flight_info[0]["airport"]["destination"]["code"]["iata"]
    return {
        "flight_number": flight_number,
        "scheduled_departure": scheduled_departure,
        "scheduled_arrival": scheduled_arrival,
        "airline_name": airline_name,
        "origin_airport": origin_airport,
        "destination_airport": destination_airport,
        "origin_timezone": origin_timezone,
        "destination_timezone": destination_timezone,
        "origin_airport_code": origin_airport_code,
        "destination_airport_code": destination_airport_code,
    }


def make_ical_event(data: dict):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//eluceo/ical//2.0/EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "REQUEST")

    event = icalendar.Event()
    event.add(
        "summary",
        f'🛫 {data["airline_name"]} {data["origin_airport_code"]} ➡️ '
        f'{data["destination_airport_code"]} {data["flight_number"]}',
    )
    origin_tz = timezone(data["origin_timezone"])
    destination_tz = timezone(data["destination_timezone"])

    dtstart = origin_tz.localize(
        datetime.strptime(data["scheduled_departure"], "%Y%m%d %H%M")
    )
    dtend = destination_tz.localize(
        datetime.strptime(data["scheduled_arrival"], "%Y%m%d %H%M")
    )

    event.add("dtstart", dtstart)
    event.add("dtend", dtend)
    event.add("location", f'{data["origin_airport"]}')
    event.add(
        "description",
        f'{data["airline_name"]} flight {data["flight_number"]} / Departs {data["origin_airport"]}, {data["origin_airport_code"]}',
    )
    event.add("dtstamp", datetime.utcnow())

    event.add("status", "CONFIRMED")

    cal.add_component(event)
    return cal.to_ical()


def save_ical_event(ical_event: bytes):
    with open("flight.ics", "wb") as f:
        f.write(ical_event)


# def make_gcal_event(data: dict) -> str:
#     base_url = "https://calendar.google.com/calendar/u/0/r/eventedit"

#     text = f'🛫 {data["airline_name"]} {data["origin_airport_code"]} ➡️ {data["destination_airport_code"]} {data["flight_number"]}'

#     origin_tz = data["origin_timezone"]
#     destination_tz = data["destination_timezone"]

#     dtstart = datetime.strptime(data["scheduled_departure"], "%Y%m%d %H%M").strftime(
#         "%Y%m%dT%H%M%S"
#     )
#     dtend = datetime.strptime(data["scheduled_arrival"], "%Y%m%d %H%M").strftime(
#         "%Y%m%dT%H%M%S"
#     )

#     dates = f"TZID={origin_tz}:{dtstart}/TZID={destination_tz}:{dtend}"

#     details = (
#         f'{data["airline_name"]} flight {data["flight_number"]} / '
#         f'Departs {data["origin_airport"]}, {data["origin_airport_code"]} / '
#         f'Origin Timezone: {data["origin_timezone"]} / '
#         f'Destination Timezone: {data["destination_timezone"]}'
#     )
#     location = data["origin_airport"]

#     gcal_url = (
#         f"{base_url}?text={text}&dates={dates}&details={details}&location={location}"
#     )

#     return gcal_url
