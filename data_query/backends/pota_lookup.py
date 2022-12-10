import datetime

import activation_info
from activation_info import ActivationInfo
from data_query.backends.generic_lookup import GenericLookup
from helpers import ModeType


class PotaLookup(GenericLookup):
    def get_activation_type_name(self):
        return "pota"

    def get_lookup_url(self, spot_limit=0):
        """spot_limit is ignored"""
        return 'https://api.pota.app/spot/activator'

    @staticmethod
    def format_freq(frequency):
        return str(float(frequency) * 1000 / 1000000)  # for floating point

    @staticmethod
    def str_to_timestamp(time_str):
        """POTA format: 2021-02-04T18:57:03"""
        return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)

    def convert_to_activation_info(self, activator_json_obj) -> ActivationInfo:
        spot_time_str = activator_json_obj["spotTime"].strip()
        spot_timestamp = PotaLookup.str_to_timestamp(spot_time_str)
        callsign = activator_json_obj["activator"].strip().upper()
        frequency = PotaLookup.format_freq(activator_json_obj["frequency"].strip())
        mode_str = activator_json_obj["mode"].strip().upper()
        mode = ModeType(mode_str)
        description = activator_json_obj["reference"].strip() + " " + activator_json_obj["locationDesc"].strip()
        return activation_info.ActivationInfo(self.get_activation_type_name(), spot_timestamp,
                                              callsign, frequency, mode, description)


if __name__ == '__main__':
    pota_lookup = PotaLookup()
    act_list = pota_lookup.query_api(spot_limit=20)
    filtered_results = pota_lookup.filter_results_by_time(act_list, time_limit=40)
    for result in filtered_results:
        print(result.to_string())
