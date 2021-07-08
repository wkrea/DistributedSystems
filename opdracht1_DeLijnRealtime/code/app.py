from flask import Flask, jsonify, Response, render_template
import json
import requests
import datetime

app = Flask(__name__, template_folder="./html/")

open_weather_key = "XXXX"

delijn_req_header = {
    'Ocp-Apim-Subscription-Key': 'XXXX'
}


def make_get_request(url, **kwargs) -> (bool, dict):
    """
        Send a GET request to the specified URL with the specified arguments. This
        will return (False, status code None) in case of a problem, or (True, status code, data) in case of
        success with "data" a dict representation of the JSON response and "status code" the HTTP status code.
    """

    print("Making call to '{}'...".format(url))
    resp = requests.get(url, **kwargs)
    print("Received response.")

    if not resp.ok:
        try:
            return False, resp.status_code, json.loads(resp.content)
        except:
            print("Severe error when receiving response. An error occurred and no error data was received!")
            return False, resp.status_code, {
                "boodschap": "unknown error (server did not respond with JSON error data)"
            }

    return True, resp.status_code, json.loads(resp.content)


@app.errorhandler(500)
def error_500(error) -> (Response, int):

    return jsonify({
        'causeErrorStatus': -1,
        'causeErrorMessage': "N/A",
        'errorMessage': "Internal server error.",
        'responseCode': 500
    }), 500

@app.route('/')
def index() -> (Response, int):
    # make overview with links to API, explanations, etc
    # make link to map

    return render_template('index.html')


@app.route('/api/provinces/')
def get_provinces() -> (Response, int):

    # make request to delijn
    get_prov_url = "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten"
    flag, status_code, data = make_get_request(get_prov_url, headers=delijn_req_header)
    if not flag:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': data["boodschap"] if "boodschap" in data else "",
            'errorMessage': "Cannot retrieve provinces from DeLijn API.",
            'responseCode': 500
        }), 500

    return jsonify({
        'provinces': [
            {
                'id': int(entiteit['entiteitnummer']),
                'name': entiteit['omschrijving'],
            } for entiteit in data["entiteiten"]
        ],
        'responseCode': 200,
    }), 200


@app.route('/api/provinces/<int:province_id>/lines/')
def get_lines(province_id: int) -> (Response, int):
    """
        Retrieve a list of lines in the specified province.
    """

    # make call to get all lines
    url_lines = "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten/{}/lijnen".format(province_id)
    flag, status_code, data_lines = make_get_request(url_lines, headers=delijn_req_header)
    if not flag:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': data_lines["boodschap"] if "boodschap" in data_lines else "",
            'errorMessage': "Cannot retrieve list of lines from DeLijn API.",
            'responseCode': 500
        }), 500

    # compile response
    return jsonify({
        'lines': [
            {
                'id': int(lijn["lijnnummer"]),
                'name': lijn['omschrijving'],
            } for lijn in data_lines["lijnen"]
        ],
        'responseCode': 200
    }), 200


@app.route('/api/provinces/<int:province_id>/lines/<int:line_id>/stops/')
def get_stops(province_id: int, line_id: int) -> (Response, int):

    """
        Retrieve a list of stops per direction for the specified line.
    """

    url_dirs = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen".format(province_id, line_id)
    flag, status_code, data_dirs = make_get_request(url_dirs, headers=delijn_req_header)
    if not flag:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': data_dirs["boodschap"] if "boodschap" in data_dirs else "",
            'errorMessage': "Cannot retrieve line directions from DeLijn API.",
            'responseCode': 500
        }), 500

    retval = {
        'dirs': [],
        'responseCode': 200
    }

    for direction in data_dirs["lijnrichtingen"]:
        dir_type = direction["richting"]
        dir_name = direction["omschrijving"]

        # determine haltes
        # retrieve list of stops with corresponding information
        url_stops = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen/{}/haltes".format(province_id, line_id, dir_type)
        flag, status_code, data_stops = make_get_request(url_stops, headers=delijn_req_header)
        if not flag:
            return jsonify({
                'causeErrorStatus': status_code,
                'causeErrorMessage': data_stops["boodschap"] if "boodschap" in data_stops else "",
                'errorMessage': "Cannot retrieve stops from DeLijn API.",
                'responseCode': 500
            }), 500

        # retrieve list of stop ids in correct order
        url_rides = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen/{}/dienstregelingen".format(province_id, line_id, dir_type)
        flag, status_code, data_rides = make_get_request(url_rides, headers=delijn_req_header)
        if not flag:
            return jsonify({
                'causeErrorStatus': status_code,
                'causeErrorMessage': data_rides["boodschap"] if "boodschap" in data_rides else "",
                'errorMessage': "Cannot retrieve schedule from DeLijn API.",
                'responseCode': 500
            }), 500

        if len(data_rides["ritDoorkomsten"]) > 0:
            dir_stops = get_sorted_stoplist(data_stops, data_rides)
        else:
            dir_stops = []  # do not return an error, since the other direction could be working fine.

        retval['dirs'].append({
            'type':  dir_type,
            'name':  dir_name,
            'stops': dir_stops
        })

    return jsonify(retval), 200


def get_sorted_stoplist(stop_data: dict, ride_data: dict) -> list:
    """
        Given data about stops and rides, retrieve a list of stops
        that are sorted in the order that they appear on the ride.
    """

    # NOTE: we only show the user stops which are part of a ride. This is correct since the animated
    # vehicles will also depend on rides and will never stop at unused stops.

    # retrieve a list of stop id's in correct order
    sorted_stop_ids = [int(stop["haltenummer"]) for stop in ride_data["ritDoorkomsten"][0]["doorkomsten"]]

    # map stop ids to stop data
    stop_map = {
        int(stop["haltenummer"]): stop for stop in stop_data["haltes"]
    }

    # compile list of stops
    return [
        {
            'id': int(halte['haltenummer']),
            'name': halte['omschrijving'],
            'city': halte['omschrijvingGemeente'],
            'coord': {
                'lat': float(halte['geoCoordinaat']['latitude']),
                'long': float(halte['geoCoordinaat']['longitude']),
            }
        } for halte in [stop_map[stop_id] for stop_id in sorted_stop_ids if stop_id in stop_map]
    ]


@app.route('/api/provinces/<int:province_id>/lines/<int:line_id>/color/')
def get_line_color(province_id: int, line_id: int) -> (Response, int):
    """
        Retrieve the color of the specified line.
    """

    url_colorcodes = "https://api.delijn.be/DLKernOpenData/api/v1/kleuren"
    flag, status_code, data_colorcodes = make_get_request(url_colorcodes, headers=delijn_req_header)
    if not flag:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': data_colorcodes["boodschap"] if "boodschap" in data_colorcodes else "",
            'errorMessage': "Cannot retrieve color codes from DeLijn API.",
            'responseCode': 500
        }), 500

    colormap = {colorcode["code"]: colorcode["hex"] for colorcode in data_colorcodes["kleuren"]}

    url_line_color = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnkleuren".format(province_id, line_id)
    flag, status_code, data_line_color = make_get_request(url_line_color, headers=delijn_req_header)
    if not flag:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': data_line_color["boodschap"] if "boodschap" in data_line_color else "",
            'errorMessage': "Cannot retrieve line colors from DeLijn API.",
            'responseCode': 500
        }), 500

    return jsonify({
        'color': "#" + colormap[data_line_color["achtergrond"]["code"]],
        'responseCode': 200
    }), 200


@app.route('/api/provinces/<int:province_id>/lines/<int:line_id>/stops/<int:stop_id>/weather/')
def get_weather(province_id: int, line_id: int, stop_id: int) -> (Response, int):
    """
        Retrieve weather information for the specified stop.
    """

    get_stop_resp, status_code = get_stops(province_id, line_id)
    stops = json.loads(get_stop_resp.get_data())  # this is fine, JSON is always returned even in case of error!

    if status_code != 200:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': stops["errorMessage"] if "errorMessage" in stops else "",
            'errorMessage': "Cannot determine weather: cannot retrieve stops from internal API.",
            'responseCode': 500
        }), 500

    for direction in stops["dirs"]:
        for stop in direction['stops']:
            if stop['id'] == stop_id:
                lat = stop["coord"]["lat"]
                long = stop["coord"]["long"]

                # make call to weather API
                url_weather = "http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&units=metric&appid={}".format(lat, long, open_weather_key)
                flag, status_code, data_weather = make_get_request(url_weather)
                if not flag:
                    return jsonify({
                        'causeErrorStatus': status_code,
                        'causeErrorMessage': data_weather["message"] if "message" in data_weather else "",
                        'errorMessage': "Cannot retrieve line colors from DeLijn API.",
                        'responseCode': 500
                    }), 500

                return jsonify({
                    'clouds':    float(data_weather["clouds"]["all"]),
                    'windSpeed': (float(data_weather["wind"]["speed"]) * 3600.0) / 1000.0,
                    'humidity':  float(data_weather["main"]["humidity"]),
                    'temp':      float(data_weather["main"]["temp"]),
                    'OWM_icon_url': "http://openweathermap.org/img/wn/{}@2x.png".format(data_weather["weather"][0]["icon"]),
                    'responseCode': 200,
                }), 200

    return jsonify({
        'causeErrorStatus': -1,
        'causeErrorMessage': "N/A",
        'errorMessage': "Specified stop does not exist according to the DeLijn API.",
        'responseCode': 500
    }), 500


@app.route('/api/provinces/<int:province_id>/lines/<int:line_id>/vehicles/')
def get_vehicles(province_id, line_id) -> (Response, int):
    """
        Retrieve a list of all vehicles on the specified line in the specified province.
    """

    get_stop_resp, status_code = get_stops(province_id, line_id)
    stops = json.loads(get_stop_resp.get_data())  # this is fine, JSON is always returned even in case of error!

    if status_code != 200:
        return jsonify({
            'causeErrorStatus': status_code,
            'causeErrorMessage': stops["errorMessage"] if "errorMessage" in stops else "",
            'errorMessage': "Cannot retrieve vehicles: cannot retrieve stops from internal API.",
            'responseCode': 500
        }), 500

    retval = {
        'dirs': [],
        'responseCode': 200
    }

    # foreach direction
    for direction in stops["dirs"]:
        dir_type = direction["type"]
        dir_name = direction["name"]

        # there are not stops for this direction => this direction is useless
        if len(direction["stops"]) == 0:
            continue

        # map stop ids to stop data
        stop_map = {
            stop["id"]: stop for stop in direction["stops"]
        }

        url_ritten = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen/{}/dienstregelingen".format(province_id, line_id, dir_type)
        flag, status_code, data_ritten = make_get_request(url_ritten, headers=delijn_req_header)
        if not flag:
            jsonify({
                'causeErrorStatus': status_code,
                'causeErrorMessage': data_ritten["boodschap"] if "boodschap" in data_ritten else "",
                'errorMessage': "Cannot retrieve schedule from DeLijn API.",
                'responseCode': 500,
            }), 500

        vehicles = []

        # foreach rit
        for rit in data_ritten["ritDoorkomsten"]:
            doorkomsten = [doorkomst for doorkomst in rit["doorkomsten"] if "dienstregelingTijdstip" in doorkomst and int(doorkomst["haltenummer"]) in stop_map]

            # rit moet minstens twee haltes hebben
            if len(doorkomsten) < 2:
                continue

            rit_nr = int(rit["ritnummer"])

            # get begin,end time of this ride
            begin_time_string = doorkomsten[0]["dienstregelingTijdstip"]
            end_time_string = doorkomsten[-1]["dienstregelingTijdstip"]

            time_format_str = "%Y-%m-%dT%H:%M:%S"
            begin_time = datetime.datetime.strptime(begin_time_string, time_format_str)
            end_time = datetime.datetime.strptime(end_time_string, time_format_str)
            current_time = datetime.datetime.now()

            # determine if rit is relevant w.r.t. current time
            if current_time.time() < begin_time.time():
                # rit is niet valid want de begintijd is not niet aangebroken
                # alle volgende ritten zullen ook niet geldig zijn want deze beginnen later
                break

            elif end_time.time() < current_time.time():
                # deze rit is niet geldig want deze is al afgelopen
                # latere ritten kunnen wel nog geldig zijn
                continue

            prev_stop_id = None
            next_stop_id = None

            # foreach halte i = 0 -> n-2
            for i in range(0, len(doorkomsten)-1):
                prev_stop = doorkomsten[i]
                next_stop = doorkomsten[i+1]

                prev_stop_id = int(prev_stop["haltenummer"])
                next_stop_id = int(next_stop["haltenummer"])

                prev_stop_time = datetime.datetime.strptime(prev_stop["dienstregelingTijdstip"], time_format_str)
                next_stop_time = datetime.datetime.strptime(next_stop["dienstregelingTijdstip"], time_format_str)

                # check if vehicle is in between stops
                if prev_stop_time.time() <= current_time.time() and current_time.time() <= next_stop_time.time():
                    break  # stop checking for other stops

            if prev_stop_id is None or next_stop_id is None:
                # vehicle was not found
                continue

            # get coords
            prev_coords = [stop_map[prev_stop_id]["coord"]["lat"], stop_map[prev_stop_id]["coord"]["long"]]
            next_coords = [stop_map[next_stop_id]["coord"]["lat"], stop_map[next_stop_id]["coord"]["long"]]

            # interpolate
            time_frac = (current_time - prev_stop_time) / (next_stop_time - prev_stop_time)

            lat_vehicle = prev_coords[0] + (next_coords[0] - prev_coords[0]) * time_frac
            long_vehicle = prev_coords[1] + (next_coords[1] - prev_coords[1]) * time_frac

            vehicles.append({
                "seqNr": rit_nr,
                "coord": {
                    "lat": lat_vehicle,
                    "long": long_vehicle
                }
            })

        retval["dirs"].append({
            "name": dir_name,
            "type": dir_type,
            "vehicles": vehicles
        })

    return jsonify(retval), 200


if __name__ == '__main__':
    app.run()
