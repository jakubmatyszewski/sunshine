import os
import logging
import logging.handlers
import requests
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import TypedDict

from imessage import imessage

load_dotenv()

dir = os.path.dirname(os.path.realpath(__file__))

console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.handlers.TimedRotatingFileHandler(f"{dir}/logs/log", when="d")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[console_handler, file_handler],
)

log = logging.getLogger(__name__)


class Coordinates(TypedDict):
    lat: float
    lon: float


WARSAW: Coordinates = {"lat": 52.2297, "lon": 21.0122}
URL = "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=sunrise,sunset,daylight_duration&timezone=auto&start_date={yday}&end_date={tday}"


def prepare_params(cords: Coordinates = WARSAW) -> dict:
    TODAY = datetime.now().strftime("%Y-%m-%d")
    YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    params = {**cords, "tday": TODAY, "yday": YESTERDAY}
    return params


def call_for_data(params: dict) -> dict:
    log.info("Fetch data from openweathermap.org")
    r = requests.get(URL.format(**params))
    r.raise_for_status()
    return r.json()


def get_sun_details(data: dict) -> tuple[float, float]:
    """Data here is represented as unix time integers."""
    d = data["daily"]
    sunrise = d["sunrise"][1].split("T")[1]
    sunset = d["sunset"][1].split("T")[1]
    yesterday_length, today_length = d["daylight_duration"]
    return sunrise, sunset, today_length, yesterday_length


def compute_difference(today_day_length: float, yesterday_day_length: float) -> str:
    diff = today_day_length - yesterday_day_length

    diff_m = int(diff / 60)  # minutes
    diff_s = int(diff % 60)  # seconds
    if diff > 0:
        return (
            f"Today is {diff_m} minute(s) and {diff_s} second(s) longer than yesterday."
        )
    elif diff < 0:
        return f"Today is {diff_m} minute(s) and {diff_s} second(s) shorter than yesterday."
    else:
        return f"It's equinox. Today will be as long as yesterday."


def send_info(payload: str) -> None:
    if PHONES := os.getenv("PHONE_NUMBER"):
        for phone in PHONES.split(","):
            phone = phone.strip()
            imessage.send(phone=phone, message=payload)
            log.info(f"iMessage sent to {phone}!")
        return
    log.warning("Data wasn't send. Please provide PHONE_NUMBER in .env")
    sys.exit(1)


def main() -> None:
    log.info(datetime.strftime(datetime.now(), "%d/%m/%Y"))
    data = call_for_data(prepare_params())
    log.info("Data collected.")
    sunrise, sunset, day_len, yday_len = get_sun_details(data)
    diff = compute_difference(day_len, yday_len)
    msg = f"""\
           Siemanko!
           Today sun rises at {sunrise} and sets at {sunset}.
           {diff}
           Smacznej kawusi!
           """.split()
    send_info(" ".join(msg))


if __name__ == "__main__":
    main()
