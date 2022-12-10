from typing import List

import helpers
from activation_info import ActivationInfo
from helpers import get_yyyymmdd_now, is_todays_date

# To put it at the same level as this file
HISTORY_FILE = helpers.local_file_path(__file__, "worked.dat")


def load_worked_history() -> List[ActivationInfo]:
    """
    Reads the file of activations we've already worked today.
    Returns an empty list if the history file is older or not readable.
    """
    try:
        with open(HISTORY_FILE) as history_file:
            saved_timestamp = history_file.readline().strip()
            if not is_todays_date(saved_timestamp):
                print("History file is older, from", saved_timestamp, "- starting fresh")
                return []
            print("Reading history file from", saved_timestamp)
            history = []
            for line in history_file:
                history_element = ActivationInfo.from_string(line.strip())
                history.append(history_element)
            print(len(history), "items in history file")
            return history
    except FileNotFoundError:
        print("No history file found:", HISTORY_FILE, "- starting fresh")
        return []
    except TypeError as te:
        print("Invalid format of", HISTORY_FILE, te, "- starting fresh")
        return []


def save_worked_history(history: List[ActivationInfo]):
    """Writes the entries worked today to a file"""
    yyyymmdd = get_yyyymmdd_now()
    with open(HISTORY_FILE, 'w') as history_file:
        history_file.write(yyyymmdd + "\n")
        for hist_item in history:
            # don't save to file if the entry is from the previous day
            if hist_item.worked_day == yyyymmdd:
                history_file.write(hist_item.to_string() + "\n")
    print("History saved to", HISTORY_FILE)


if __name__ == '__main__':
    def test_load():
        history = load_worked_history()
        print("Fetched history:", len(history))
        for hist_item in history:
            print(hist_item)


    def test_save():
        save_worked_history([])

    test_load()
