import io
from datetime import datetime, timedelta

import pandas as pd
import icalendar
from pyflightdata import FlightData
from pytz import timezone

f = FlightData()

# test_config
# flight_number = "EW9464"
# date = "2024-12-20"


def make_ics_from_selected_df_index(df: pd.DataFrame, index: int) -> bytes:
    data = df.iloc[index].to_dict()
    ical_event = make_ical_event(data)
    ics = save_ical_event(ical_event)
    return ics


def get_flight(flight_number: str, date: str) -> pd.DataFrame:
    flight_number = parse_flight_number(flight_number)
    date = parse_date(date)
    flight_info = find_flights_with_date(flight_number, date)
    if not flight_info:
        flight_info = find_flight_no_date(flight_number)
        flight_info = drop_ununique_flights(flight_info)
        df = pd.DataFrame(
            [parse_flight_info(flight_info, i) for i in range(len(flight_info))]
        )
        df["is_guess"] = True
        for i in range(len(df)):
            df.loc[i] = move_flight_date(df.loc[i], date)
        return df
    else:
        if len(flight_info) > 1:
            df = pd.DataFrame(
                [parse_flight_info(flight_info, i) for i in range(len(flight_info))]
            )
            df["is_guess"] = False
            return df
        else:
            df = pd.DataFrame([parse_flight_info(flight_info, 0)])
            df["is_guess"] = False
            return df


def parse_flight_info(flight_info: dict, chosen_flight_index: int) -> dict:
    n = chosen_flight_index
    flight_number = flight_info[n]["identification"]["number"]["default"]
    scheduled_departure = (
        flight_info[n]["time"]["scheduled"]["departure_date"]
        + " "
        + flight_info[n]["time"]["scheduled"]["departure_time"]
    )
    scheduled_arrival = (
        flight_info[n]["time"]["scheduled"]["arrival_date"]
        + " "
        + flight_info[n]["time"]["scheduled"]["arrival_time"]
    )
    airline_name = flight_info[n]["airline"]["name"]
    origin_airport = flight_info[n]["airport"]["origin"]["name"]
    destination_airport = flight_info[n]["airport"]["destination"]["name"]
    origin_timezone = flight_info[n]["airport"]["origin"]["timezone"]["name"]
    destination_timezone = flight_info[n]["airport"]["destination"]["timezone"]["name"]
    origin_airport_code = flight_info[n]["airport"]["origin"]["code"]["iata"]
    destination_airport_code = flight_info[n]["airport"]["destination"]["code"]["iata"]
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


def parse_date(date: str) -> str:
    return datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d")


def parse_flight_number(flight_number: str) -> str:
    return "".join(filter(str.isalnum, flight_number.upper()))


def ics_to_bytes(ics: icalendar.Event) -> bytes:
    return bytes


def find_flights_with_date(flight_number: str, date: str) -> dict:
    flight_info = f.get_flight_for_date(flight_number, date)
    return flight_info


def find_flight_no_date(flight_number: str):
    flight_info = f.get_history_by_flight_number(flight_number)
    if not flight_info:
        raise ValueError("No flight information found for the given flight number.")
    return flight_info


def drop_ununique_flights(flight_info: dict) -> dict:
    # only keeps flights which have a different scheduled departure time (ignoring date)
    unique_departure_times = set()
    unique_flights = []
    for flight in flight_info:
        departure_time = flight["time"]["scheduled"]["departure_time"]
        if departure_time not in unique_departure_times:
            unique_departure_times.add(departure_time)
            unique_flights.append(flight)
    flight_info = unique_flights
    return flight_info


def move_flight_date(flight_info: dict, date: str):
    scheduled_departure = datetime.strptime(
        flight_info["scheduled_departure"], "%Y%m%d %H%M"
    )
    scheduled_arrival = datetime.strptime(
        flight_info["scheduled_arrival"], "%Y%m%d %H%M"
    )

    # Calculate the day difference
    date = datetime.strptime(date, "%Y%m%d").date()
    day_difference = (date - scheduled_departure.date()).days

    # Adjust the scheduled departure and arrival dates
    if day_difference != 0:
        scheduled_departure = scheduled_departure + timedelta(days=day_difference)
        scheduled_arrival = scheduled_arrival + timedelta(days=day_difference)
    else:
        scheduled_departure = datetime.combine(date, scheduled_departure.time())
        scheduled_arrival = datetime.combine(date, scheduled_arrival.time())

    flight_info["scheduled_departure"] = scheduled_departure.strftime("%Y%m%d %H%M")
    flight_info["scheduled_arrival"] = scheduled_arrival.strftime("%Y%m%d %H%M")

    return flight_info


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
    destination_tz = timezone(
        data["destination_timezone"]
    )  # todo: I think it's doing timezones wrong

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
    event.add("dtstamp", datetime.now())

    event.add("status", "CONFIRMED")

    cal.add_component(event)
    return cal.to_ical()


def save_ical_event(ical_event: bytes):
    ical_bytes = io.BytesIO(ical_event)
    return ical_bytes
