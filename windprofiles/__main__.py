import argparse
from .user.config import set_api_key, get_api_key

parser = argparse.ArgumentParser()
parser.add_argument(
    "--set-google-maps-api-key",
    default=None,
    metavar="KEY",
    help="Set value of Google Maps API key (for use in elevation and timezone requests)",
)
parser.add_argument(
    "--show-google-maps-api-key",
    "--get-google-maps-api-key",
    action="store_true",
    help="Print current value of Google Maps API key",
)

args = vars(parser.parse_args())
if (key := args.get("set_google_maps_api_key")) is not None:
    set_api_key("gmaps", key)
if args.get("show_google_maps_api_key"):
    print(get_api_key("gmaps"))
