from mcp.server.fastmcp import FastMCP
import bus
import json
import common
mcp = FastMCP("bus-tools-server")

# @mcp.tool()
# def get_bus_stop_details(bus_stop_code: int) -> dict:
#     """Get the bus arrival time for the provided bus stop code and bus service number.
#     Args:
#     BusStopCode: unique 5-digit identifier for this bus stop. Example: 01012
#     Returns a json"""

#     b = common.sanitize_number(bus_stop_code)
#     with open('LTABusStop.geojson', 'r') as file:
#         data = json.load(file)
#         matching_feature = next(
#             (feature for feature in data['features'] if feature['properties'].get('BUS_STOP_NUM') == b), 
#             None  # Default value if no match is found
#         )
#         if matching_feature:
#             return(json.dumps(matching_feature, indent=4))
#         else:
#             return(f"Bus stop {bus_stop_code} not found.")    

@mcp.tool()
def get_bus_arrival(bus_stop_code: int, serivice_no: int = None) -> dict:
    """Get the bus arrival time for the provided bus stop code and bus service number. If only bus stop code is provided, retrieves all buses for this bus stop.
    Args:
    bus_stop_code: unique 5-digit identifier for this bus stop. Example: 01012
    serivice_no: bus service number. Example: 196

    Returns a json formatted as follows:
        ServiceNo: Bus service number 15
        Operator Public Transport Operator Codes: SBST (for SBS Transit), SMRT (for SMRT Corporation), TTS (for Tower Transit Singapore), GAS (for Go Ahead Singapore)
        NextBus: Nearest bus arriving
        NextBus2: 2nd nearest bus arriving (blank if there is only 1 bus arriving)
        NextBus3: 3rd nearest bus arriving (blank if there is only 1 bus arriving)
        OriginCode: bus stop code of the first bus stop where this bus started its service. Example: 77009
        DestinationCode: bus stop code of the last bus stop where this bus will terminate its service. Example: 77131
        EstimatedArrival: estimated Date-time of arrival expressed in the UTC standard, GMT+8 for Singapore Standard Time (SST) Example: 2017-04-29T07:20:24+08:00
        Monitored: Indicates if the bus arrival time is based on the schedule from operators. 0 (based on schedule), 1 (based on bus location). Example: 1
        Latitude: Latitude coordinates of this bus. Example: 1.42117943692586
        Longitude: Longitude coordinates of this bus. Example: 103.831477233098
        VisitNumber: Ordinal value of the nth visit of this vehicle at this bus stop. 1 (1st), 2 (2nd). Example: 1
        Load: occupancy: SEA (Seats Available), SDA (Standing Available), LSD (Limited Standing). Example: SEA
        Feature: bus features. WAB (is wheel-chair accessible). Example: WAB
        Type: Vehicle type. SD (Single Deck), DD (Double Deck), BD (Bendy). Example: SD
    """    
    return bus.get_bus_arrival(bus_stop_code, serivice_no)

@mcp.tool()
def get_bus_stop(bus_stop_code: int) -> dict:
    """Get the bus stop information for provided code.
    Args:
    bus_stop_code: unique 5-digit identifier for this bus stop. Example: 01012

    Returns a json formatted as follows:
        BusStopCode: The unique 5-digit identifier for this bus stop. Example: 01012        
        RoadName: The road on which this bus stop is located. Example: Victoria St
        Description: Landmarks next to the bus stop (if any) to aid in identifying this bus stop Example: Hotel Grand Pacific
        Latitude: Latitude Location coordinates for this bus stop. Example: 1.29685
        Longitude: Longitude Location coordinates for this bus stop. Example: 103.853
    """
    return bus.get_bus_stop(bus_stop_code)


@mcp.tool()
def get_weather(city: str) -> str:
    """Get the current weather for a city.
    Args:
    string city
    """
    # In a real server, you'd call a weather API here
    return f"The weather in {city} is sunny, 28°C."

@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Get a multi-day weather forecast for a city.
    Args:
    string city
    integer days
    """
    return f"{days}-day forecast for {city}: mostly snowy with light rain on day 2."

if __name__ == "__main__":
    mcp.run()