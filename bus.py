import os
import requests
from dotenv import load_dotenv
import common
import json
loaded = load_dotenv()
LTA_API_KEY = os.getenv('LTA_API_KEY')
api_arr='https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival'
api_stops='https://datamall2.mytransport.sg/ltaodataservice/BusStops'


def reduce_json(obj, keep_keys):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            reduced_v = reduce_json(v, keep_keys)
            if k in keep_keys:
                result[k] = reduced_v
            elif reduced_v not in (None, {}, []):
                # unwanted key, but it contained wanted data deeper inside
                # merge it up rather than nesting under the unwanted key
                if isinstance(reduced_v, dict):
                    result.update(reduced_v)
                elif isinstance(reduced_v, list):
                    # list of items, e.g. Services: [...]
                    return reduced_v  # bubble the whole list up
        return result
    elif isinstance(obj, list):
        reduced_list = [reduce_json(item, keep_keys) for item in obj]
        return [item for item in reduced_list if item not in (None, {}, [])]
    else:
        return obj

def get_bus_arrival(bus_stop_code,service_no = None):
    b = common.sanitize_number(bus_stop_code)
    if not b:
        return "Please provide a 5 digit number for the bus stop."
    params = {'BusStopCode': b,"ServiceNo":common.sanitize_number(service_no)}
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }

    response = requests.get(api_arr, headers=headers, params=params)
    print(response.json())
    keep = {"ServiceNo", "EstimatedArrival", "NextBus", "NextBus2", "NextBus3"}    
    reduced = reduce_json(response.json(),keep)
    return reduced

def get_bus_stop(bus_stop_code):
    b = common.sanitize_number(bus_stop_code)
    if not b:
        return "Please provide a 5 digit number for the bus stop."
    params = {'BusStopCode': b}
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }
    keep = {"RoadName", "Description"}
    response = requests.get(api_stops, headers=headers, params=params)
    reduced = reduce_json(response.json(),keep)
    return reduced
 
if __name__ == "__main__":
    result = get_bus_stop(93131)
    # result = get_bus_arrival(93131)
    print(result)