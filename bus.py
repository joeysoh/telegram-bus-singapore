import os
import requests
from dotenv import load_dotenv
import common
loaded = load_dotenv()
LTA_API_KEY = os.getenv('LTA_API_KEY')
api_arr='https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival'
api_stops='https://datamall2.mytransport.sg/ltaodataservice/BusStops'


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
    print(f"Status Code: {response.status_code}")
    return response.json()

def get_bus_stop(bus_stop_code):
    b = common.sanitize_number(bus_stop_code)
    if not b:
        return "Please provide a 5 digit number for the bus stop."
    params = {'BusStopCode': b}
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }
    response = requests.get(api_stops, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    return response.json()

 
if __name__ == "__main__":
    result = get_bus_stop(93131)
    # result = get_bus_arrival(93131)
    print(result)