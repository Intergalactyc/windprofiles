# External APIs
## Google Maps API
Currently used by `data.elevation` ([Google Maps Elevation API](https://developers.google.com/maps/documentation/elevation)) and `data.timezone` ([Google Maps Timezone API](https://developers.google.com/maps/documentation/timezone/)).

See the Google Cloud [Quick Start guide](console.cloud.google.com/google/maps-apis/start?) for instructions on obtaining a key. Using a free key you will be able to make 5000 requests per service each month.

To set: `python -m windprofiles --set-google-maps-api-key <KEY>`

To print: `python -m windprofiles --get-google-maps-api-key`
