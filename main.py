import os
import logging
import logging.handlers
import requests
import sys
from datetime import datetime
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
API_KEY = os.getenv("API_KEY")
URL = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={key}"


def call_for_data(cords: dict[str, float] = WARSAW) -> dict:
    log.info("Fetch data from openweathermap.org")
    url = URL.format(**{**cords, "key": API_KEY})
    r = requests.get(url)
    r.raise_for_status()
    return r.json()


def get_sun_details(data: dict) -> tuple[int, int, int]:
    """Data here is represented as unix time integers."""
    d = data["current"]
    sunrise = d["sunrise"]
    sunset = d["sunset"]
    day_length = sunset - sunrise
    return sunrise, sunset, day_length


def save(day_length: int) -> None:
    with open(f"{dir}/data", "w+") as f:
        f.write(f"{day_length}")
    log.info("Today's data is saved!")


def compute_difference(current_day_length: int) -> str:
    try:
        with open(f"{dir}/data") as f:
            archive = int(f.read())
    except Exception as e:
        log.error("Failed to read yesterday's data!")
        return ""
    else:
        diff = current_day_length - archive

        diff_m = int(diff / 60)  # minutes
        diff_s = diff % 60  # seconds
        if diff > 0:
            return f"Today is {diff_m} minute(s) and {diff_s} second(s) longer than yesterday."
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
    if not API_KEY:
        log.error("openweathermap API_KEY is missing.")
        sys.exit(1)
    data = call_for_data()
    log.info("Data collected.")
    sunrise, sunset, day_len = get_sun_details(data)
    diff = compute_difference(day_len)
    save(day_len)
    msg = f"""\
           Siemanko!
           Today sun rises at {datetime.strftime(datetime.fromtimestamp(sunrise), "%H:%M:%S")}\
           and sets at {datetime.strftime(datetime.fromtimestamp(sunset), "%H:%M:%S")}.
           {diff}
           Smacznej kawusi!
           """.split()
    send_info(" ".join(msg))


if __name__ == "__main__":
    main()
