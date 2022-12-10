import abc
from typing import List

import requests

from activation_info import ActivationInfo


class GenericLookup:
    @abc.abstractmethod
    def get_activation_type_name(self):
        raise NotImplementedError("abstract")

    def query_api(self, spot_limit):
        if spot_limit < 1 or spot_limit > 100:
            print("Defaulting spot_limit to 100")
            spot_limit = 100
        url = self.get_lookup_url(spot_limit)
        print("url", url)
        try:
            r = requests.get(url)
        except requests.exceptions.RequestException as re:
            print("Problem hitting", url, re)
            raise QueryError(self.__class__.__name__)
        act_list = r.json()
        if r.status_code != 200:
            print("Problem hitting", url, r.status_code)
            raise QueryError(self.__class__.__name__)
        return act_list

    @abc.abstractmethod
    def get_lookup_url(self, spot_limit: int):
        raise NotImplementedError("abstract")

    @abc.abstractmethod
    def convert_to_activation_info(self, activator_json_obj) -> ActivationInfo:
        raise NotImplementedError("abstract")

    def filter_results_by_time(self, act_list, time_limit) -> List[ActivationInfo]:
        print(act_list)
        filtered_results = []
        for activator in act_list:
            activation_info = self.convert_to_activation_info(activator)
            print(activation_info.to_string())
            if time_limit and activation_info.spot_age_mins() > time_limit:
                print("too old, age is:", activation_info.spot_age_mins())
                continue
            print("match is within time limit")
            filtered_results.append(activation_info)
        return filtered_results


class QueryError(Exception):
    pass
