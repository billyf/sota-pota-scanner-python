from configparser import ConfigParser

import helpers
from helpers import ModeFilter


class Settings:
    CONFIG_FILE = helpers.local_file_path(__file__, "config.ini")
    MODE_SECTION = "MODE_FILTERS"
    SETTINGS_SECTION = "SETTINGS"
    REFRESH_INTERVAL_KEY = "refresh_interval"
    MAX_AGE_KEY = "max_age"

    def __init__(self):
        config = ConfigParser()

        config.read(self.CONFIG_FILE)

        self.refresh_interval = config.getint(self.SETTINGS_SECTION, self.REFRESH_INTERVAL_KEY, fallback=2)
        self.max_age = config.getint(self.SETTINGS_SECTION, self.MAX_AGE_KEY, fallback=30)

        self.mode_filters = []
        for mode in ModeFilter:
            mode_enabled = config.getboolean(self.MODE_SECTION, mode.name, fallback=False)
            if mode_enabled or not config.has_section(self.MODE_SECTION):  # show all modes when no saved config
                self.mode_filters.append(mode)

    def save_mode_filters(self, mode_filters_dict):
        config = ConfigParser()
        config.read(self.CONFIG_FILE)
        if not config.has_section(self.MODE_SECTION):
            config.add_section(self.MODE_SECTION)
        for mode_key in mode_filters_dict:
            config.set(self.MODE_SECTION, mode_key, str(mode_filters_dict[mode_key].get()))
        with open(self.CONFIG_FILE, 'w') as f:
            config.write(f)
        print("Updated mode filters in", self.CONFIG_FILE)

    def save_other_preferences(self, refresh_interval_ms, max_age):
        config = ConfigParser()
        config.read(self.CONFIG_FILE)
        if not config.has_section(self.SETTINGS_SECTION):
            config.add_section(self.SETTINGS_SECTION)
        refresh_interval_min = int(refresh_interval_ms / 60000)
        config.set(self.SETTINGS_SECTION, self.REFRESH_INTERVAL_KEY, str(refresh_interval_min))
        config.set(self.SETTINGS_SECTION, self.MAX_AGE_KEY, str(max_age))
        with open(self.CONFIG_FILE, 'w') as f:
            config.write(f)
        print("Updated interval and max age in", self.CONFIG_FILE)
