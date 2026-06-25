import os
import requests
from dotenv import load_dotenv
loaded = load_dotenv()
LTA_API_KEY = os.getenv('LTA_API_KEY')
api_arr='https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival'
api_stops='https://datamall2.mytransport.sg/ltaodataservice/BusStops'

def getBusArrival(BusStopCode,ServiceNo = None):
    params = {'BusStopCode': BusStopCode,"ServiceNo":ServiceNo}
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }

    response = requests.get(api_arr, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    return response.json()

def getBusStop(busstopCode):
    params = {'BusStopCode': busstopCode}
    headers = {
        'AccountKey': LTA_API_KEY,
        'accept': 'application/json'
    }

    # response = requests.get(api_arr, headers=headers, params=params)
    response = requests.get(api_stops, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    return response.json()

 
if __name__ == "__main__":
    # result = getBusStop()
    result = getBusArrival(93131)
    print(result)