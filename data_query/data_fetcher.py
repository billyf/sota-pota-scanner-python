from data_query.backends import pota_lookup
from data_query.backends import sota_lookup
from data_query.backends.generic_lookup import QueryError


class DataFetcher:
    def __init__(self):
        self.all_lookups = [
            sota_lookup.SotaLookup(),
            pota_lookup.PotaLookup()
        ]

    def retrieve_filtered_spots_by_time(self, spot_limit, time_limit=None):
        spots = []
        errors = []
        for lookup in self.all_lookups:
            try:
                act_list = lookup.query_api(spot_limit)
                filtered_results = lookup.filter_results_by_time(act_list, time_limit)
                spots.extend(filtered_results)
            except QueryError as qe:
                print("Problem querying API for", type(lookup).__name__)
                errors.append(qe)
        return spots, errors

