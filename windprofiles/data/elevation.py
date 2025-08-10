from ..user.config import get_api_key
from .request import urlopen_with_cache, APIException


def get_elevation(lat, lon):
    apikey = get_api_key("gmaps")
    if apikey is None:
        raise APIException(
            "No Google Maps API key found. Use `python -m windprofiles config --set-google-maps-api-key` to configure."
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


# def get_elevation_raster(lat, lon)
