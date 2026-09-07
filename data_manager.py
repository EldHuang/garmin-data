import json
import calendar
import statistics
from datetime import datetime, timedelta, date


class DataManager:

    def __init__(self):

        with open(
            "./garmin_all_data/all_garmin_data_dump.json",
            "r",
            encoding="utf-8"
        ) as file:
            self.data = json.load(file)

        self.training_stats = self.data["training_stats"]
        self.pr = self.data["personal_records"]
        self.sleep = self.data["sleep"]
        self.steps = self.data["steps"]
        self.daily_stats = self.data["daily_stats"]

        # Last month
        today = datetime.now()
        last_month_date = today - timedelta(days=today.day)

        self.last_month_year = (
            f"{last_month_date.year}-{last_month_date.month:02d}"
        )

    # =========================================================
    # VO2 MAX
    # =========================================================

    def vo2(self):

        vo2_values = []
        training_status = []

        for day_data in self.training_stats.values():

            vo2_data = None
            status_data = None

            try:
                vo2_data = (
                    day_data["status"]
                    ["mostRecentVO2Max"]
                    ["generic"]
                )
            except (KeyError, TypeError):
                pass

            try:
                status_data = tuple(
                    day_data["status"]
                    ["mostRecentTrainingStatus"]
                    ["latestTrainingStatusData"]
                    .values()
                )[0]
            except (KeyError, TypeError, IndexError):
                pass

            if vo2_data is not None:
                vo2_values.append(
                    vo2_data["vo2MaxPreciseValue"]
                )

            if status_data is not None:

                phrase = status_data[
                    "trainingStatusFeedbackPhrase"
                ]

                training_status.append(
                    phrase.split("_")[0]
                )

        if not vo2_values:
            return {
                "high": None,
                "low": None,
                "avg": None,
                "values": [],
                "training_status": []
            }

        return {
            "high": max(vo2_values),
            "low": min(vo2_values),
            "avg": round(
                statistics.mean(vo2_values),
                2
            ),
            "values": vo2_values,
            "training_status": training_status
        }

    # =========================================================
    # PERSONAL RECORDS
    # =========================================================

    def personal_records(self):

        filtered_data = {
            "steps": [],
            "running": [],
            "cycling": [],
            "swimming": [],
            "strength": []
        }

        abbreviations = {
            "run": "running",
            "cy": "cycling",
            "swi": "swimming"
        }

        for record in self.pr:

            if self.last_month_year not in record[
                "prStartTimeGmtFormatted"
            ]:
                continue

            activity_type = record["activityType"]
            value = record["value"]
            activity_name = record["activityName"]

            append_to_type = None

            if activity_type is not None:

                for key, category in abbreviations.items():

                    if key in activity_type:
                        append_to_type = category
                        break

            else:

                activity_name = "Steps"
                append_to_type = "steps"

                if value > 222800:
                    activity_name = "Most Steps in a Month"

                elif value > 65000:
                    activity_name = "Most Steps in a Week"

                elif value > 12800:
                    activity_name = "Most Steps in a Day"

                else:
                    activity_name = "Unknown"

            if append_to_type:

                filtered_data[append_to_type].append({
                    "Activity": activity_name,
                    "Value": value
                })

        return filtered_data

    # =========================================================
    # SLEEP
    # =========================================================

    def sleep_data(self):

        sleep_scores = {}
        resting_hr = {}
        sleep_len = {}
        hrv = {}

        for day in self.sleep:

            values = day["values"]
            datex = day["calendarDate"]

            if values.get("sleepScore") is not None:
                sleep_scores[datex] = values["sleepScore"]

            if values.get("restingHeartRate") is not None:
                resting_hr[datex] = values["restingHeartRate"]

            if values.get("totalSleepTimeInSeconds") is not None:

                sleep_len[datex] = round(
                    values["totalSleepTimeInSeconds"]
                    / 60
                    / 60,
                    2
                )

            if values.get("avgOvernightHrv") is not None:
                hrv[datex] = values["avgOvernightHrv"]

        def stats(dictionary):

            values = list(dictionary.values())

            if not values:
                return {
                    "avg": None,
                    "max": None,
                    "min": None
                }

            max_value = max(values)
            min_value = min(values)

            max_date = next(
                k for k, v in dictionary.items()
                if v == max_value
            )

            min_date = next(
                k for k, v in dictionary.items()
                if v == min_value
            )

            return {
                "avg": round(
                    statistics.mean(values),
                    2
                ),
                "max": {
                    "date": max_date,
                    "value": max_value
                },
                "min": {
                    "date": min_date,
                    "value": min_value
                }
            }

        return {
            "score": stats(sleep_scores),
            "sleep_length": stats(sleep_len),
            "resting_hr": {
                "avg": round(
                    statistics.mean(resting_hr.values()),
                    2
                ) if resting_hr else None
            },
            "hrv": {
                "avg": round(
                    statistics.mean(hrv.values()),
                    2
                ) if hrv else None
            },
            "daily": {
                "scores": sleep_scores,
                "length": sleep_len,
                "resting_hr": resting_hr,
                "hrv": hrv
            }
        }

    # =========================================================
    # STEPS
    # =========================================================

    def steps_data(self):

        steps = {}
        distance = {}

        total_steps = 0
        total_distance_meter = 0
        total_goal = 0

        for day in self.steps:

            datex = day["calendarDate"]

            day_steps = day["totalSteps"]
            day_distance = day["totalDistance"]
            day_goal = day["stepGoal"]

            total_steps += day_steps
            total_distance_meter += day_distance
            total_goal += day_goal

            steps[datex] = day_steps
            distance[datex] = day_distance

        def get_extreme(dictionary, mode):

            values = list(dictionary.values())

            if mode == "max":
                value = max(values)
            else:
                value = min(values)

            day = next(
                k for k, v in dictionary.items()
                if v == value
            )

            return {
                "date": day,
                "value": value
            }

        return {

            "totals": {
                "steps": total_steps,
                "distance_miles": round(
                    total_distance_meter * 0.000621371,
                    2
                )
            },

            "goal": {
                "percent": round(
                    (total_steps / total_goal) * 100,
                    2
                ) if total_goal else None
            },

            "steps": {
                "avg": round(
                    statistics.mean(steps.values()),
                    2
                ),
                "max": get_extreme(steps, "max"),
                "min": get_extreme(steps, "min"),
                "daily": steps
            },

            "distance": {
                "avg": round(
                    statistics.mean(distance.values())
                    * 0.000621371,
                    2
                ),
                "max": {
                    "date": get_extreme(
                        distance,
                        "max"
                    )["date"],
                    "value": round(
                        get_extreme(
                            distance,
                            "max"
                        )["value"] * 0.000621371,
                        2
                    )
                },
                "min": {
                    "date": get_extreme(
                        distance,
                        "min"
                    )["date"],
                    "value": round(
                        get_extreme(
                            distance,
                            "min"
                        )["value"] * 0.000621371,
                        2
                    )
                },
                "daily": distance
            }
        }

    # =========================================================
    # FLOORS
    # =========================================================

    def floors_data(self):

        floors_up = {}
        floors_down = {}

        for day, values in self.daily_stats.items():

            summary = values["summary"]

            floors_up[day] = summary["floorsAscended"]
            floors_down[day] = summary["floorsDescended"]

        return {
            "avg": round(
                statistics.mean(
                    floors_up.values()
                ),
                2
            ),
            "max": {
                "date": max(
                    floors_up,
                    key=floors_up.get
                ),
                "value": max(
                    floors_up.values()
                )
            },
            "daily_up": floors_up,
            "daily_down": floors_down
        }

    # =========================================================
    # RESPIRATION
    # =========================================================

    def respiration_data(self):

        highest = {}
        lowest = {}
        waking = {}

        for day, values in self.daily_stats.items():

            summary = values["summary"]

            highest[day] = (
                summary["highestRespirationValue"]
            )

            lowest[day] = (
                summary["lowestRespirationValue"]
            )

            waking[day] = (
                summary["avgWakingRespirationValue"]
            )

        return {
            "high": max(highest.values()),
            "avg_high": round(
                statistics.mean(
                    highest.values()
                ),
                2
            ),

            "low": min(lowest.values()),
            "avg_low": round(
                statistics.mean(
                    lowest.values()
                ),
                2
            ),

            "avg_awake": round(
                statistics.mean(
                    waking.values()
                ),
                2
            ),

            "daily": {
                "high": highest,
                "low": lowest,
                "waking": waking
            }
        }

    # =========================================================
    # STRESS
    # =========================================================

    def stress_data(self):

        avg_stress = {}
        max_stress = {}

        low_duration = 0
        high_duration = 0

        for day, values in self.daily_stats.items():

            summary = values["summary"]

            avg_stress[day] = (
                summary["averageStressLevel"]
            )

            max_stress[day] = (
                summary["maxStressLevel"]
            )

            low_duration += (
                summary["lowStressDuration"]
            )

            high_duration += (
                summary["highStressDuration"]
            )

        last_month = (
            date.today().replace(day=1)
            - timedelta(days=1)
        )

        days = calendar.monthrange(
            last_month.year,
            last_month.month
        )[1]

        total_seconds = days * 24 * 60 * 60

        return {
            "percent_low": round(
                low_duration / total_seconds * 100,
                2
            ),

            "percent_high": round(
                high_duration / total_seconds * 100,
                2
            ),

            "avg_avg": round(
                statistics.mean(
                    avg_stress.values()
                ),
                2
            ),

            "avg_max": round(
                statistics.mean(
                    max_stress.values()
                ),
                2
            ),

            "max": {
                "date": max(
                    max_stress,
                    key=max_stress.get
                ),
                "value": max(
                    max_stress.values()
                )
            },

            "daily": {
                "average": avg_stress,
                "maximum": max_stress
            }
        }

    # =========================================================
    # BODY BATTERY
    # =========================================================

    def body_battery_data(self):

        charge = {}
        drain = {}
        lowest = {}
        highest = {}

        for day, values in self.daily_stats.items():

            summary = values["summary"]

            charge[day] = (
                summary["bodyBatteryChargedValue"]
            )

            drain[day] = (
                summary["bodyBatteryDrainedValue"]
            )

            lowest[day] = (
                summary["bodyBatteryLowestValue"]
            )

            highest[day] = (
                summary["bodyBatteryHighestValue"]
            )

        return {
            "avg_charge": round(
                statistics.mean(
                    charge.values()
                ),
                2
            ),

            "avg_drain": round(
                statistics.mean(
                    drain.values()
                ),
                2
            ),

            "low": {
                "avg": round(
                    statistics.mean(
                        lowest.values()
                    ),
                    2
                ),
                "min": min(lowest.values()),
                "median": statistics.median(
                    lowest.values()
                )
            },

            "high": {
                "avg": round(
                    statistics.mean(
                        highest.values()
                    ),
                    2
                ),
                "max": max(highest.values())
            },

            "daily": {
                "charge": charge,
                "drain": drain,
                "low": lowest,
                "high": highest
            }
        }

    # =========================================================
    # HEART RATE
    # =========================================================

    def heart_rate(self):

        maximum = {}
        minimum = {}
        resting = {}

        for day, values in self.daily_stats.items():

            summary = values["summary"]

            maximum[day] = summary["maxHeartRate"]
            minimum[day] = summary["minHeartRate"]
            resting[day] = summary["restingHeartRate"]

        return {

            "max": {
                "max": max(maximum.values()),
                "avg": round(
                    statistics.mean(
                        maximum.values()
                    ),
                    2
                ),
                "daily": maximum
            },

            "min": {
                "avg": round(
                    statistics.mean(
                        minimum.values()
                    ),
                    2
                ),
                "daily": minimum
            },

            "resting": {
                "avg": round(
                    statistics.mean(
                        resting.values()
                    ),
                    2
                ),
                "daily": resting
            }
        }

    # =========================================================
    # MAIN
    # =========================================================

    def main(self):

        return {
            "vo2": self.vo2(),
            "personal_records": self.personal_records(),
            "sleep": self.sleep_data(),
            "steps": self.steps_data(),
            "floors": self.floors_data(),
            "respiration": self.respiration_data(),
            "stress": self.stress_data(),
            "body_battery": self.body_battery_data(),
            "heart_rate": self.heart_rate()
        }
