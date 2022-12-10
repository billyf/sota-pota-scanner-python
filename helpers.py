import datetime
import os
from enum import Enum
from pathlib import Path
from typing import List


def get_yyyymmdd_now() -> str:
    return datetime.datetime.utcnow().strftime('%Y%m%d')


def is_todays_date(yyyymmdd) -> bool:
    """Returns true if listed_date is the same UTC day as right now"""
    now_yyyymmdd = get_yyyymmdd_now()
    return now_yyyymmdd == yyyymmdd


def local_file_path(sourcefile: str, filename: str) -> str:
    """Returns the full path to filename, at the same level as sourcefile"""
    return str(Path(sourcefile).resolve().parent) + os.sep + filename


DATA_MODES = ["PSK31", "RTTY", "MFSK", "JT65", "JT9", "FT8", "FT4", "JS8CALL"]
"""Add other modes to this list which count as as ModeFilter.DATA"""


class ModeType:
    def __init__(self, mode_str: str):
        self.mode_str = mode_str
        for filter_option in ModeFilter:
            if mode_str.upper() == filter_option.value.upper():
                self.mode_filter = filter_option
                return
        for data_mode in DATA_MODES:
            if mode_str.upper() == data_mode.upper():
                self.mode_filter = ModeFilter.DATA
                return
        self.mode_filter = ModeFilter.OTHER


class ModeFilter(Enum):
    AM = "AM"
    CW = "CW"
    DATA = "Data"
    DV = "DV"
    FM = "FM"
    SSB = "SSB"
    OTHER = "Other"


def in_mode_filters(mode: ModeType, mode_filters: List[ModeFilter]) -> bool:
    for allowed_mode in mode_filters:
        if mode.mode_filter == allowed_mode:
            return True
    return False
