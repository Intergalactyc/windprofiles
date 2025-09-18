from windprofiles.user.config import get_api_key
from windprofiles.data.request import urlopen_with_cache, APIException

from time import time


def get_elevation(lat, lon):
    apikey = get_api_key("gmaps")
    if apikey is None:
        raise APIException(
            "No Google Maps API key found. Use `python -m windprofiles --set-google-maps-api-key` to configure."
        )
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    results = urlopen_with_cache(
        f"{url}?locations={lat},{lon}&key={apikey}",
        parameters=["gmaps-elevation", lat, lon],
    )
    try:
        if results is not None:
            elevation = results.get("results")[0].get("elevation")
            return elevation
        else:
            print("HTTP GET request failed.")
            return None
    except ValueError as e:
        print(f"JSON decode failed: {e}")


def get_timezone(lat, lon):
    apikey = get_api_key("gmaps")
    if apikey is None:
        raise APIException(
            "No Google Maps API key found. Use `python -m windprofiles --set-google-maps-api-key` to configure."
        )
    url = "https://maps.googleapis.com/maps/api/timezone/json"
    timestamp = int(
        time()
    )  # we don't actually care about dst but it requires a timestamp so just use current time
    results = urlopen_with_cache(
        f"{url}?location={lat},{lon}&timestamp={timestamp}&key={apikey}",
        parameters=["gmaps-timezone", lat, lon],
    )
    try:
        if results is not None and 0 < len(results):
            timezone = results.get("timeZoneId")
            return timezone
        else:
            print("HTTP GET request failed.")
            return None
    except Exception as e:
        print(f"JSON decode failed: {e}")
        return None
