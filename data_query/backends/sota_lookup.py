import datetime

import activation_info
from activation_info import ActivationInfo
from data_query.backends.generic_lookup import GenericLookup
from helpers import ModeType


class SotaLookup(GenericLookup):
    def get_activation_type_name(self):
        return "sota"

    def get_lookup_url(self, spot_limit: int) -> str:
        return f'https://api2.sota.org.uk/api/spots/{spot_limit}/all'

    @staticmethod
    def str_to_timestamp(time_str: str) -> datetime:
        """
        SOTA format: 2021-02-04T19:03:49.83
        or           2022-12-03T00:51:00
        """
        time_str = time_str.split('.')[0]  # sometimes microseconds are present
        return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)

    def convert_to_activation_info(self, activator_json_obj) -> ActivationInfo:
        spot_time_str = activator_json_obj["timeStamp"].strip()
        spot_timestamp = SotaLookup.str_to_timestamp(spot_time_str)
        callsign = activator_json_obj["activatorCallsign"].strip().upper()
        frequency = activator_json_obj["frequency"].strip()
        mode_str = activator_json_obj["mode"].strip().upper()
        mode = ModeType(mode_str)
        description = activator_json_obj["associationCode"].strip() + "/" + activator_json_obj["summitCode"].strip()
        return activation_info.ActivationInfo(self.get_activation_type_name(), spot_timestamp,
                                              callsign, frequency, mode, description)


if __name__ == '__main__':
    sota_lookup = SotaLookup()
    act_list = sota_lookup.query_api(spot_limit=20)
    filtered_results = sota_lookup.filter_results_by_time(act_list, time_limit=40)
    for result in filtered_results:
        print(result.to_string())
