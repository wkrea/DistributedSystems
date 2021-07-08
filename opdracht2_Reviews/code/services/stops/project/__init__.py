import sys
import os
import enum
import json

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
import requests

############### FLASK INIT & CONFIG ###############

delijn_req_header = {
    'Ocp-Apim-Subscription-Key': 'XXXX'
}

app = Flask(__name__)

app_settings = os.getenv('APP_SETTINGS')
app.config.from_object(app_settings)

def make_get_request(url:str, **kwargs) -> (bool, dict):
    """
        Send a GET request to the specified URL with the specified arguments. 

        The return value is a tuple (bool, status, data). 'bool' will be true in case the call returns code 200, False otherwise.
        'status' contains the HTTP status code of the response. 'data' contains the reponse data, or error data in case of an error.

        Note: 'headers' parameter contains a dict with header data.
    """

    print("Making call to '{}'...".format(url))
    resp = requests.get(url, **kwargs)
    print("Received response.")

    return resp.ok, resp.status_code, json.loads(resp.content)

############### API ###############

api = Api(app)


class StopsHW(Resource):
    """
        Hello-world API endpoint
    """

    def get(self):
        return {
            'responseCode': 200,
            'message': 'Hello world!'
        }, 200


class GetProvinces(Resource):
    """
        API endpoint to retrieve a list of provinces.
    """
    
    def get(self):
        try:
            # make request to delijn
            get_prov_url = "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten"
            flag, status_code, data = make_get_request(get_prov_url, headers=delijn_req_header)
            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data["boodschap"] if "boodschap" in data else "N/A",
                    'errorMessage': "Cannot retrieve provinces from DeLijn API.",
                    'responseCode': 500
                }, 500

            return {
                'provinces': [
                    {
                        'id': int(entiteit['entiteitnummer']),
                        'name': entiteit['omschrijving'],
                    } for entiteit in data["entiteiten"]
                ],
                'responseCode': 200,
            }, 200

        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve provinces: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve provinces: unknown exception.', 
                'responseCode': 500
            }, 500


class GetStopsProvince(Resource):
    """
        API endpoint to retrieve a list of stops for the specified province.
    """
    
    def get(self, province_id):
        try:
            # make request to delijn
            get_stops_url = "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten/{}/haltes".format(province_id)

            flag, status_code, data_stops = make_get_request(get_stops_url, headers=delijn_req_header)

            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data_stops["boodschap"] if "boodschap" in data_stops else "N/A",
                    'errorMessage': "Cannot retrieve stops from DeLijn API.",
                    'responseCode': 500
                }, 500

            return {
                'responseCode': 200,
                'stops': [
                    {
                        "stopId": int(halte['haltenummer']),
                        "stopName": halte['omschrijving'],
                        "cityName": halte['omschrijvingGemeente'],
                    } for halte in data_stops['haltes'] if 'omschrijving' in halte and 'omschrijvingGemeente' in halte
                ]
            }, 200

        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown exception.', 
                'responseCode': 500
            }, 500


class GetLines(Resource):
    """
        API endpoint to retrieve a list of lines for the specified province.
    """
    
    def get(self, province_id):
        try:
            # make call to get all lines
            url_lines = "https://api.delijn.be/DLKernOpenData/api/v1/entiteiten/{}/lijnen".format(province_id)
            flag, status_code, data_lines = make_get_request(url_lines, headers=delijn_req_header)
            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data_lines["boodschap"] if "boodschap" in data_lines else "N/A",
                    'errorMessage': "Cannot retrieve list of lines from DeLijn API.",
                    'responseCode': 500
                }, 500

            # compile response
            return {
                'lines': [
                    {
                        'id': int(lijn["lijnnummer"]),
                        'name': lijn['omschrijving'],
                    } for lijn in data_lines["lijnen"]
                ],
                'responseCode': 200
            }, 200

        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve lines: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve lines: unknown exception.', 
                'responseCode': 500
            }, 500


class GetStopsLine(Resource):
    """
        API endpoint to retrieve a list of stops for the specified line.
    """
    
    def get(self, province_id:int, line_id:int):
        try:
            url_dirs = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen".format(province_id, line_id)
            flag, status_code, data_dirs = make_get_request(url_dirs, headers=delijn_req_header)
            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data_dirs["boodschap"] if "boodschap" in data_dirs else "",
                    'errorMessage': "Cannot retrieve line directions from DeLijn API.",
                    'responseCode': 500
                }, 500

            retval = {
                'responseCode': 200,
                'stops': []
            }

            # keep track of the stops that were already added
            processed_ids = set()

            for direction in data_dirs["lijnrichtingen"]:
                url_stops = "https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{}/{}/lijnrichtingen/{}/haltes".format(province_id, line_id, direction["richting"])
                flag, status_code, data_stops = make_get_request(url_stops, headers=delijn_req_header)

                if not flag:
                    return {
                        'causeErrorStatus': status_code,
                        'causeErrorMessage': data_stops["boodschap"] if "boodschap" in data_stops else "",
                        'errorMessage': "Cannot retrieve stops from DeLijn API.",
                        'responseCode': 500
                    }, 500

                for stop in data_stops['haltes']:
                    halte_id = int(stop['haltenummer'])

                    if not halte_id in processed_ids:
                        retval['stops'].append({
                            'stopId':   int(stop['haltenummer']),
                            'stopName': stop['omschrijving'],
                            'cityName': stop['omschrijvingGemeente']
                        })

            return retval, 200
        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown exception.', 
                'responseCode': 500
            }, 500


class GetCities(Resource):
    """
        API endpoint to retrieve a list of cities.
    """
    
    def get(self):
        try:
            url_cities = "https://api.delijn.be/DLKernOpenData/api/v1/gemeenten"
            flag, status_code, data_cities = make_get_request(url_cities, headers=delijn_req_header)

            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data_lines["boodschap"] if "boodschap" in data_lines else "N/A",
                    'errorMessage': "Cannot retrieve list of cities from DeLijn API.",
                    'responseCode': 500
                }, 500

            cities = [
                {
                    'cityId': int(city['gemeentenummer']),
                    'cityName': city['omschrijving'],
                } for city in data_cities['gemeenten'] if city['gemeentenummer'] != -1
            ]

            # sort cities in alphabetical order
            cities.sort(key=lambda city: city['cityName'])

            return {
                'cities': cities,
                'responseCode': 200,
            }, 200

        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve cities: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve cities: unknown exception.', 
                'responseCode': 500
            }, 500


class GetStopsCity(Resource):
    """
        API endpoint to retrieve list of stops for the specified city.
    """

    def get(self, city_id):
        try:
            url_stops = "https://api.delijn.be/DLKernOpenData/api/v1/gemeenten/{}/haltes".format(city_id)

            flag, status_code, data_stops = make_get_request(url_stops, headers=delijn_req_header)

            if not flag:
                return {
                    'causeErrorStatus': status_code,
                    'causeErrorMessage': data_stops["boodschap"] if "boodschap" in data_stops else "N/A",
                    'errorMessage': "Cannot retrieve stops from DeLijn API.",
                    'responseCode': 500
                }, 500

            return {
                'responseCode': 200,
                'stops': [
                    {
                        "stopId": int(halte['haltenummer']),
                        "stopName": halte['omschrijving'],
                        "cityName": halte['omschrijvingGemeente'],
                    } for halte in data_stops['haltes']
                ]
            }, 200

        except Exception as e:
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve stops: unknown exception.', 
                'responseCode': 500
            }, 500


api.add_resource(StopsHW,     '/hello_world/')

api.add_resource(GetProvinces,     '/provinces/')
api.add_resource(GetStopsProvince, '/provinces/<int:province_id>/stops/')

api.add_resource(GetLines,         '/provinces/<int:province_id>/lines/')
api.add_resource(GetStopsLine,     '/provinces/<int:province_id>/lines/<int:line_id>/stops/')

api.add_resource(GetCities,        '/cities/')
api.add_resource(GetStopsCity,     '/cities/<int:city_id>/stops/')
