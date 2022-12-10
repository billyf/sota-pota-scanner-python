import datetime

from helpers import is_todays_date, ModeType


class ActivationInfo:
    """Represents an activation listing, plus worked_day if we've moved them to the bottom list"""
    def __init__(self, activation_type: str, spot_time: datetime, callsign: str, frequency: str,
                 mode: ModeType, description: str, worked_day: str = ""):
        self.activation_type = activation_type
        self.spot_time = spot_time
        self.callsign = callsign
        self.frequency = frequency
        self.mode = mode
        self.description = description
        self.worked_day = worked_day

    SPOT_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def to_string(self) -> str:
        spot_time_str = self.spot_time.strftime(self.SPOT_TIMESTAMP_FORMAT)
        return "|".join([self.activation_type, spot_time_str, self.callsign, self.frequency,
                         self.mode.mode_str, self.description, self.worked_day])

    @staticmethod
    def from_string(str_val: str):
        line_parts = str_val.split("|")
        spot_time_str = line_parts[1]
        spot_timestamp = datetime.datetime.strptime(spot_time_str, ActivationInfo.SPOT_TIMESTAMP_FORMAT).replace(tzinfo=datetime.timezone.utc)
        mode = ModeType(line_parts[4])
        return ActivationInfo(line_parts[0], spot_timestamp, line_parts[2], line_parts[3], mode, line_parts[5], line_parts[6])

    def worked_today(self) -> bool:
        return is_todays_date(self.worked_day)

    def spot_age_mins(self) -> int:
        return int((datetime.datetime.now(datetime.timezone.utc) - self.spot_time).total_seconds() / 60)
