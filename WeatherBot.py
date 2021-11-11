import requests
import json
import os

class WeatherBot() {
    def __init__(self):
        self.us_state_to_abbrev = {
            "alabama": "AL",
            "alaska": "AK",
            "arizona": "AZ",
            "arkansas": "AR",
            "california": "CA",
            "colorado": "CO",
            "connecticut": "CT",
            "delaware": "DE",
            "florida": "FL",
            "georgia": "GA",
            "hawaii": "HI",
            "idaho": "ID",
            "illinois": "IL",
            "indiana": "IN",
            "iowa": "IA",
            "iansas": "KS",
            "kentucky": "KY",
            "louisiana": "LA",
            "maine": "ME",
            "maryland": "MD",
            "massachusetts": "MA",
            "michigan": "MI",
            "minnesota": "MN",
            "mississippi": "MS",
            "missouri": "MO",
            "montana": "MT",
            "nebraska": "NE",
            "nevada": "NV",
            "new hampshire": "NH",
            "new jersey": "NJ",
            "new mexico": "NM",
            "new york": "NY",
            "north carolina": "NC",
            "north dakota": "ND",
            "ohio": "OH",
            "oklahoma": "OK",
            "oregon": "OR",
            "pennsylvania": "PA",
            "rhode rsland": "RI",
            "south carolina": "SC",
            "south dakota": "SD",
            "tennessee": "TN",
            "texas": "TX",
            "utah": "UT",
            "vermont": "VT",
            "virginia": "VA",
            "washington": "WA",
            "west virginia": "WV",
            "wisconsin": "WI",
            "wyoming": "WY",
            "district of columbia": "DC",
            "american samoa": "AS",
            "guam": "GU",
            "northern mariana islands": "MP",
            "puerto rico": "PR",
            "united states minor outlying islands": "UM",
            "u.s. virgin islands": "VI",
        }
    
        self.api_key = os.environ["weather_key"]
    
    #returns json data for city and state in US
    def get_current_weather(city, state):
        payload = {"q":city+","+"US-"self.us_state_to_abbrev[state], "appid":self.api_key, "units":"imperial"}
        return format_weather_json(requests.get("https://api.openweathermap.org/data/2.5/weather", params = payload))
    
    def format_weather_json(weather_json):
        str = "__Weather in " + weather_json["name"] + "__\n"
            + "Temperature: " + str(weather_json["main"]["temp"]) + '\u00b0'+ " F\n"
            + "Feels like: " + str(weather_json["main"]["feels_like"]) + '\u00b0'+ " F\n"
            + "Humidity: " + str(weather_json["main"]["humidity"]) + "%\n"
            + "Cloudiness/rain: " + weather_json["weather"]["main"] + " - " + weather_json["weather"]["description"] + "\n"
            + "Wind: " + weather_json["wind"]["speed"] + " MPH, " weather_json["wind"]["deg"] + '\u00b0\ + "\n"
            + "Wind gusts: " + weather_json["wind"]["gust"] + "MPH"
        
        return str
        
}
