import os
import json
import time
import random
import datetime

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError
)

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
TOKEN_FILE = "./garmin_all_data/garmin_session_token.json"
OUTPUT_FOLDER = "garmin_all_data"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "all_garmin_data_dump.json")

MIN_DELAY = 1.0
MAX_DELAY = 2.5
MAX_RETRIES = 3
RATE_LIMIT_WAIT = 60

def get_previous_month_dates():
    today = datetime.date.today()
    first_day = today.replace(day=1)
    last_day = first_day - datetime.timedelta(days=1)
    return last_day.replace(day=1), last_day

def wait():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def is_rate_limit_error(e):
    text = str(e).lower()
    return (
        isinstance(e, GarminConnectTooManyRequestsError)
        or "429" in text
        or "too many requests" in text
        or "rate limit" in text
        or "rate-limited" in text
    )

def is_auth_error(e):
    text = str(e).lower()
    return (
        isinstance(e, GarminConnectAuthenticationError)
        or "401" in text
        or "403" in text
        or "authentication" in text
        or "username and password are required" in text
    )

def authenticate(client):
    print("Authenticating with Garmin...")

    if os.path.exists(TOKEN_FILE):
        print(f"Found saved Garmin session: {TOKEN_FILE}")
        print("Attempting to use saved session...")
        try:
            client.login(TOKEN_FILE)
            print("Saved Garmin session accepted.")
            return True
        except GarminConnectTooManyRequestsError as e:
            print(f"ERROR: Garmin rate-limited the saved session: {e}")
            return False
        except GarminConnectConnectionError as e:
            print(f"ERROR: Could not connect to Garmin: {e}")
            return False
        except GarminConnectAuthenticationError as e:
            print(f"Saved session is invalid or expired: {e}")
            print("Attempting fresh login...")
        except Exception as e:
            print(f"Saved session failed: {e}")
            print("Attempting fresh login...")

    if not EMAIL or not PASSWORD:
        print("ERROR: EMAIL or PASSWORD environment variable is missing.")
        return False

    print("Attempting fresh Garmin login...")

    try:
        client.login()
        print("Fresh Garmin login successful.")
        try:
            client.dump(TOKEN_FILE)
            print(f"Saved new Garmin session to {TOKEN_FILE}")
        except Exception as e:
            print(f"WARNING: Could not save Garmin session: {e}")
        return True

    except GarminConnectTooManyRequestsError as e:
        print(f"ERROR: Garmin rate-limited this connection (429): {e}")
        print("Do not repeatedly retry immediately.")
        return False
    except GarminConnectAuthenticationError as e:
        print(f"ERROR: Garmin authentication failed: {e}")
        return False
    except GarminConnectConnectionError as e:
        print(f"ERROR: Could not connect to Garmin Connect: {e}")
        return False
    except Exception as e:
        print(f"ERROR during Garmin login: {e}")
        return False

def safe_request(function, description):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return True, function()
        except Exception as e:
            if is_rate_limit_error(e):
                print(f"[RATE LIMITED] {description}")
                if attempt < MAX_RETRIES:
                    print(f"Waiting {RATE_LIMIT_WAIT} seconds before retrying...")
                    time.sleep(RATE_LIMIT_WAIT)
                    continue
                print(f"Maximum rate-limit retries reached for {description}.")
                return False, None

            if is_auth_error(e):
                print(f"[AUTHENTICATION FAILED] {description}: {e}")
                return False, None

            print(f"[FAILED] {description} (attempt {attempt}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return False, None

    return False, None

def fetch_daily_data(client, date):
    data = {"date": date}
    success = True

    requests = {
        "summary": lambda: client.get_user_summary(date),
    }

    for name, function in requests.items():
        wait()
        ok, result = safe_request(function, f"{name} ({date})")
        if ok:
            data[name] = result
        else:
            data[name] = None
            success = False

    return data, success

def fetch_training_data(client, date):
    data = {"date": date}
    success = True

    if int(date.split("-")[2]) % 3 == 0:
        requests = {
            "status": lambda: client.get_training_status(date),
            "v02_max": lambda: client.get_max_metrics(date)
        }

        for name, function in requests.items():
            wait()
            ok, result = safe_request(function, f"{name} ({date})")
            data[name] = result if ok else None
            if not ok:
                success = False

    return data, success

def collect_data():
    print("Starting Garmin data export...")

    if not EMAIL or not PASSWORD:
        print("ERROR: EMAIL or PASSWORD environment variable is missing.")
        return

    client = Garmin(EMAIL, PASSWORD)

    if not authenticate(client):
        print("EXPORT FAILED: Garmin authentication was unsuccessful.")
        return

    start_date, end_date = get_previous_month_dates()
    print(f"Fetching data from {start_date} through {end_date}...")

    output = {
        "exported_at": datetime.datetime.now().isoformat(),
        "daily_stats": {},
        "steps": [],
        "sleep": [],
        "training_stats": {},
        "personal_records": [],
        "export_status": {"complete": True, "failed_requests": []}
    }

    failed = []
    curr = start_date
    total_days = (end_date - start_date).days + 1
    day_number = 0

    while curr <= end_date:
        day_number += 1
        date = curr.isoformat()
        print(f"[{day_number}/{total_days}] Processing {date}...")

        daily_data, daily_ok = fetch_daily_data(client, date)
        output["daily_stats"][date] = daily_data
        if not daily_ok:
            failed.append(f"Daily data: {date}")

        training_data, training_ok = fetch_training_data(client, date)
        output["training_stats"][date] = training_data
        if not training_ok:
            failed.append(f"Training data: {date}")

        curr += datetime.timedelta(days=1)

    print("Fetching personal records...")
    wait()
    ok, data = safe_request(client.get_personal_record, "Personal records")
    if ok:
        output["personal_records"] = data
    else:
        failed.append("Personal records")

    print("Fetching daily steps...")
    wait()
    ok, data = safe_request(
        lambda: client.get_daily_steps(start_date.isoformat(), end_date.isoformat()),
        "Daily steps"
    )
    if ok:
        output["steps"] = data
    else:
        failed.append("Daily steps")

    print("Fetching daily sleep...")
    wait()
    ok, data = safe_request(
        lambda: client.get_sleep_daily(start_date.isoformat(), end_date.isoformat()),
        "Daily sleep"
    )
    if ok:
        output["sleep"] = data
    else:
        failed.append("Daily sleep")

    output["export_status"]["complete"] = len(failed) == 0
    output["export_status"]["failed_requests"] = failed

    try:
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        temp_file = OUTPUT_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(output, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_file, OUTPUT_FILE)

    except Exception as e:
        print(f"EXPORT FAILED: Could not write JSON file: {e}")
        return

    print()

    if not failed:
        print("SUCCESS: Authentication and all requested Garmin data succeeded.")
        print(f"Export saved to: {OUTPUT_FILE}")
    else:
        print(f"EXPORT COMPLETED WITH ERRORS: {len(failed)} operation(s) failed.")
        print(f"Partial export saved to: {OUTPUT_FILE}")
        print("Failed operations:")
        for item in failed:
            print(f"  - {item}")
