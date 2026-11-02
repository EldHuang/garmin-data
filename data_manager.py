import json
import calendar
import statistics
from datetime import datetime, timedelta, date


class DataManager:
    """Load Garmin data and calculate summaries while safely ignoring nulls."""

    def __init__(self):
        with open(
            "./garmin_all_data/all_garmin_data_dump.json",
            "r",
            encoding="utf-8",
        ) as file:
            self.data = json.load(file)

        self.training_stats = self.data.get("training_stats") or {}
        self.pr = self.data.get("personal_records") or []
        self.sleep = self.data.get("sleep") or []
        self.steps = self.data.get("steps") or []
        self.daily_stats = self.data.get("daily_stats") or {}

        # Last completed calendar month
        today = datetime.now()
        last_month_date = today - timedelta(days=today.day)
        self.last_month_year = (
            f"{last_month_date.year}-{last_month_date.month:02d}"
        )

    # =========================================================
    # NULL-SAFE HELPERS
    # =========================================================

    @staticmethod
    def _number(value):
        """Return a number only when value is not None."""
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    @classmethod
    def _values(cls, values):
        """Filter null and non-numeric values from an iterable."""
        return [
            cls._number(value)
            for value in values
            if cls._number(value) is not None
        ]

    @classmethod
    def _mean(cls, values):
        values = cls._values(values)
        return round(statistics.mean(values), 2) if values else None

    @classmethod
    def _extreme(cls, dictionary, mode):
        """Return date/value for max or min, or None if no valid values."""
        valid = {
            key: cls._number(value)
            for key, value in dictionary.items()
            if cls._number(value) is not None
        }

        if not valid:
            return None

        value = max(valid.values()) if mode == "max" else min(valid.values())
        day = next(key for key, item in valid.items() if item == value)
        return {"date": day, "value": value}

    @staticmethod
    def _summary(values):
        """Summary statistics for a date-to-value dictionary."""
        valid = {
            key: value
            for key, value in values.items()
            if value is not None
        }

        if not valid:
            return {"avg": None, "max": None, "min": None}

        max_value = max(valid.values())
        min_value = min(valid.values())
        max_date = next(k for k, v in valid.items() if v == max_value)
        min_date = next(k for k, v in valid.items() if v == min_value)

        return {
            "avg": DataManager._mean(valid.values()),
            "max": {"date": max_date, "value": max_value},
            "min": {"date": min_date, "value": min_value},
        }

    @staticmethod
    def _summary_for_day(values):
        """Safely retrieve a day's summary dictionary."""
        if not isinstance(values, dict):
            return {}
        summary = values.get("summary")
        return summary if isinstance(summary, dict) else {}

    # =========================================================
    # VO2 MAX
    # =========================================================

    def vo2(self):
        vo2_values = []
        training_status = []

        for day_data in self.training_stats.values():
            if not isinstance(day_data, dict):
                continue

            status = day_data.get("status") or {}
            if not isinstance(status, dict):
                continue

            vo2_data = (
                (status.get("mostRecentVO2Max") or {}).get("generic")
                if isinstance(status.get("mostRecentVO2Max"), dict)
                else None
            )

            if isinstance(vo2_data, dict):
                value = self._number(vo2_data.get("vo2MaxPreciseValue"))
                if value is not None:
                    vo2_values.append(value)

            training_data = status.get("mostRecentTrainingStatus") or {}
            latest = (
                training_data.get("latestTrainingStatusData")
                if isinstance(training_data, dict)
                else None
            )

            if isinstance(latest, dict) and latest:
                status_data = next(iter(latest.values()), None)
                if isinstance(status_data, dict):
                    phrase = status_data.get("trainingStatusFeedbackPhrase")
                    if isinstance(phrase, str) and phrase:
                        training_status.append(phrase.split("_")[0])

        if not vo2_values:
            return {
                "high": None,
                "low": None,
                "avg": None,
                "values": [],
                "training_status": training_status,
            }

        return {
            "high": max(vo2_values),
            "low": min(vo2_values),
            "avg": self._mean(vo2_values),
            "values": vo2_values,
            "training_status": training_status,
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
            "strength": [],
        }

        abbreviations = {
            "run": "running",
            "cy": "cycling",
            "swi": "swimming",
            "strength": "strength",
        }

        for record in self.pr:
            if not isinstance(record, dict):
                continue

            record_date = record.get("prStartTimeGmtFormatted")
            if not isinstance(record_date, str) or self.last_month_year not in record_date:
                continue

            activity_type = record.get("activityType")
            value = record.get("value")
            activity_name = record.get("activityName") or "Unknown"
            append_to_type = None

            if activity_type:
                activity_type = str(activity_type).lower()
                for key, category in abbreviations.items():
                    if key in activity_type:
                        append_to_type = category
                        break
            else:
                activity_name = "Steps"
                append_to_type = "steps"
                numeric_value = self._number(value)

                if numeric_value is None:
                    activity_name = "Unknown"
                elif numeric_value > 222800:
                    activity_name = "Most Steps in a Month"
                elif numeric_value > 65000:
                    activity_name = "Most Steps in a Week"
                elif numeric_value > 12800:
                    activity_name = "Most Steps in a Day"
                else:
                    activity_name = "Unknown"

            if append_to_type:
                filtered_data[append_to_type].append({
                    "Activity": activity_name,
                    "Value": value,
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
            if not isinstance(day, dict):
                continue

            values = day.get("values") or {}
            datex = day.get("calendarDate")
            if not isinstance(values, dict) or datex is None:
                continue

            score = self._number(values.get("sleepScore"))
            if score is not None:
                sleep_scores[datex] = score

            resting = self._number(values.get("restingHeartRate"))
            if resting is not None:
                resting_hr[datex] = resting

            sleep_seconds = self._number(values.get("totalSleepTimeInSeconds"))
            if sleep_seconds is not None:
                sleep_len[datex] = round(sleep_seconds / 3600, 2)

            overnight_hrv = self._number(values.get("avgOvernightHrv"))
            if overnight_hrv is not None:
                hrv[datex] = overnight_hrv

        return {
            "score": self._summary(sleep_scores),
            "sleep_length": self._summary(sleep_len),
            "resting_hr": {"avg": self._mean(resting_hr.values())},
            "hrv": {"avg": self._mean(hrv.values())},
            "daily": {
                "scores": sleep_scores,
                "length": sleep_len,
                "resting_hr": resting_hr,
                "hrv": hrv,
            },
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
            if not isinstance(day, dict):
                continue

            datex = day.get("calendarDate")
            if datex is None:
                continue

            day_steps = self._number(day.get("totalSteps"))
            day_distance = self._number(day.get("totalDistance"))
            day_goal = self._number(day.get("stepGoal"))

            # Missing values contribute zero to totals.
            total_steps += day_steps if day_steps is not None else 0
            total_distance_meter += day_distance if day_distance is not None else 0
            total_goal += day_goal if day_goal is not None else 0

            # Missing daily values are omitted from averages/extremes.
            if day_steps is not None:
                steps[datex] = day_steps
            if day_distance is not None:
                distance[datex] = day_distance

        max_steps = self._extreme(steps, "max")
        min_steps = self._extreme(steps, "min")
        max_distance = self._extreme(distance, "max")
        min_distance = self._extreme(distance, "min")

        return {
            "totals": {
                "steps": total_steps,
                "distance_miles": round(total_distance_meter * 0.000621371, 2),
            },
            "goal": {
                "percent": round((total_steps / total_goal) * 100, 2)
                if total_goal else None
            },
            "steps": {
                "avg": self._mean(steps.values()),
                "max": max_steps,
                "min": min_steps,
                "daily": steps,
            },
            "distance": {
                "avg": (
                    round(statistics.mean(distance.values()) * 0.000621371, 2)
                    if distance else None
                ),
                "max": (
                    {
                        "date": max_distance["date"],
                        "value": round(max_distance["value"] * 0.000621371, 2),
                    }
                    if max_distance else None
                ),
                "min": (
                    {
                        "date": min_distance["date"],
                        "value": round(min_distance["value"] * 0.000621371, 2),
                    }
                    if min_distance else None
                ),
                "daily": distance,
            },
        }

    # =========================================================
    # FLOORS
    # =========================================================

    def floors_data(self):
        floors_up = {}
        floors_down = {}

        for day, values in self.daily_stats.items():
            summary = self._summary_for_day(values)

            up = self._number(summary.get("floorsAscended"))
            down = self._number(summary.get("floorsDescended"))

            if up is not None:
                floors_up[day] = up
            if down is not None:
                floors_down[day] = down

        max_up = self._extreme(floors_up, "max")

        return {
            "avg": self._mean(floors_up.values()),
            "max": max_up,
            "daily_up": floors_up,
            "daily_down": floors_down,
        }

    # =========================================================
    # RESPIRATION
    # =========================================================

    def respiration_data(self):
        highest = {}
        lowest = {}
        waking = {}

        for day, values in self.daily_stats.items():
            summary = self._summary_for_day(values)

            high = self._number(summary.get("highestRespirationValue"))
            low = self._number(summary.get("lowestRespirationValue"))
            awake = self._number(summary.get("avgWakingRespirationValue"))

            if high is not None:
                highest[day] = high
            if low is not None:
                lowest[day] = low
            if awake is not None:
                waking[day] = awake

        high_extreme = self._extreme(highest, "max")
        low_extreme = self._extreme(lowest, "min")

        return {
            "high": high_extreme["value"] if high_extreme else None,
            "avg_high": self._mean(highest.values()),
            "low": low_extreme["value"] if low_extreme else None,
            "avg_low": self._mean(lowest.values()),
            "avg_awake": self._mean(waking.values()),
            "daily": {
                "high": highest,
                "low": lowest,
                "waking": waking,
            },
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
            summary = self._summary_for_day(values)

            average = self._number(summary.get("averageStressLevel"))
            maximum = self._number(summary.get("maxStressLevel"))
            low = self._number(summary.get("lowStressDuration"))
            high = self._number(summary.get("highStressDuration"))

            if average is not None:
                avg_stress[day] = average
            if maximum is not None:
                max_stress[day] = maximum

            low_duration += low if low is not None else 0
            high_duration += high if high is not None else 0

        last_month = date.today().replace(day=1) - timedelta(days=1)
        days = calendar.monthrange(last_month.year, last_month.month)[1]
        total_seconds = days * 24 * 60 * 60

        max_stress_extreme = self._extreme(max_stress, "max")

        return {
            "percent_low": round(low_duration / total_seconds * 100, 2)
            if total_seconds else None,
            "percent_high": round(high_duration / total_seconds * 100, 2)
            if total_seconds else None,
            "avg_avg": self._mean(avg_stress.values()),
            "avg_max": self._mean(max_stress.values()),
            "max": max_stress_extreme,
            "daily": {
                "average": avg_stress,
                "maximum": max_stress,
            },
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
            summary = self._summary_for_day(values)

            fields = {
                "charge": ("bodyBatteryChargedValue", charge),
                "drain": ("bodyBatteryDrainedValue", drain),
                "low": ("bodyBatteryLowestValue", lowest),
                "high": ("bodyBatteryHighestValue", highest),
            }

            for field, (source_key, target) in fields.items():
                value = self._number(summary.get(source_key))
                if value is not None:
                    target[day] = value

        low_extreme = self._extreme(lowest, "min")
        high_extreme = self._extreme(highest, "max")

        return {
            "avg_charge": self._mean(charge.values()),
            "avg_drain": self._mean(drain.values()),
            "low": {
                "avg": self._mean(lowest.values()),
                "min": low_extreme["value"] if low_extreme else None,
                "median": (
                    round(statistics.median(lowest.values()), 2)
                    if lowest else None
                ),
            },
            "high": {
                "avg": self._mean(highest.values()),
                "max": high_extreme["value"] if high_extreme else None,
            },
            "daily": {
                "charge": charge,
                "drain": drain,
                "low": lowest,
                "high": highest,
            },
        }

    # =========================================================
    # HEART RATE
    # =========================================================

    def heart_rate(self):
        maximum = {}
        minimum = {}
        resting = {}

        for day, values in self.daily_stats.items():
            summary = self._summary_for_day(values)

            max_hr = self._number(summary.get("maxHeartRate"))
            min_hr = self._number(summary.get("minHeartRate"))
            resting_hr = self._number(summary.get("restingHeartRate"))

            if max_hr is not None:
                maximum[day] = max_hr
            if min_hr is not None:
                minimum[day] = min_hr
            if resting_hr is not None:
                resting[day] = resting_hr

        max_extreme = self._extreme(maximum, "max")

        return {
            "max": {
                "max": max_extreme["value"] if max_extreme else None,
                "avg": self._mean(maximum.values()),
                "daily": maximum,
            },
            "min": {
                "avg": self._mean(minimum.values()),
                "daily": minimum,
            },
            "resting": {
                "avg": self._mean(resting.values()),
                "daily": resting,
            },
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
            "heart_rate": self.heart_rate(),
        }
