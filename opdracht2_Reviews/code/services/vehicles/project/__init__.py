import sys
import os
import enum
import json

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from passlib.hash import sha256_crypt
import requests

############### FLASK INIT & CONFIG ###############

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


def make_post_request(url:str, **kwargs):
    """
        Send a POST request to the specified URL with the specified arguments. The 'data' argument is
        a dict that contains (key, value) pairs which will be sent as form data. All other keyword arguments will be passed to the requests library.

        The return value is a tuple (bool, status, data). 'bool' will be true in case the call returns code 200, False otherwise.
        'status' contains the HTTP status code of the response. 'data' contains the reponse data, or error data in case of an error.

        Note: 'headers' parameter contains a dict with header data.
    """

    print("Making call to '{}'...".format(url))
    resp = requests.post(url, **kwargs)
    print("Received response.")

    return resp.ok, resp.status_code, json.loads(resp.content)


def make_delete_request(url:str, **kwargs):
    """
        Send a DELETE request to the specified URL with the specified arguments. The 'data' argument is
        a dict that contains (key, value) pairs which will be sent as form data. All other keyword arguments will be passed to the requests library.

        The return value is a tuple (bool, status, data). 'bool' will be true in case the call returns code 200, False otherwise.
        'status' contains the HTTP status code of the response. 'data' contains the reponse data, or error data in case of an error.

        Note: 'headers' parameter contains a dict with header data.
    """

    print("Making call to '{}'...".format(url))
    resp = requests.delete(url, **kwargs)
    print("Received response.")

    return resp.ok, resp.status_code, json.loads(resp.content)

############### DB SETTINGS ###############

# init DB
db = SQLAlchemy(app)

class EnumVehicleType(enum.Enum):
    BUS  = "Bus"
    TRAM = "Tram"

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    vehicle_nr   = db.Column(db.String(50), primary_key=True, nullable=False, unique=True)
    vehicle_type = db.Column(db.Enum(EnumVehicleType), nullable=False)
    owner_id     = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<Vehicle vehicle_nr={}, vehicle_type={}, owner_id={}>".format(self.vehicle_nr, self.vehicle_type, self.owner_id)

############### API ###############

api = Api(app)


class VehiclesHW(Resource):
    """
        Hello-world API endpoint
    """

    def get(self):
        return {
            'responseCode': 200,
            'message': 'Hello world!'
        }, 200


class CreateVehicle(Resource):
    """
        API endpoint to create a vehicle.
    """

    def post(self):
        try:

            if not 'username' in request.headers:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'username' entry in HTTP request header.",
                    'responseCode': 400
                }, 400

            if not 'password' in request.headers:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'password' entry in HTTP request header.",
                    'responseCode': 400
                }, 400

            # authenticate user
            # NOTE: this can cause a 400 error if this data is not present!
            username = request.headers['username']
            password = request.headers['password']

            # authenticate user
            flag, status_code, auth_data = make_get_request('http://users:5000/auth/', headers={'username': username, 'password': password})

            if not flag:
                # ERROR while authenticating user => "Cannot authenticate user"
                return {
                    'causeErrorMessage': auth_data['errorMessage'],
                    'causeErrorStatus': status_code,
                    'errorMessage': 'Error while authenticating user.',
                    'responseCode': 500
                }, 500
            elif not auth_data['result']:
                # user is not valid
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Cannot authenticate user: ' + auth_data['reason'] + ' Please specify a valid username and password.',
                    'responseCode': 400
                }, 400

            if not 'vehicleNr' in request.form:
                # vehicleNr not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'vehicleNr' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            if not 'vehicleType' in request.form:
                # vehicleType not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'vehicleType' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            # retrieve vehicle info
            vehicle_nr   = request.form["vehicleNr"]
            vehicle_type = EnumVehicleType[request.form["vehicleType"]]
            owner_id     = auth_data['userId']

            # add to DB
            new_vehicle = Vehicle(vehicle_nr=vehicle_nr, vehicle_type=vehicle_type, owner_id=owner_id)

            db.session.add(new_vehicle)
            db.session.commit()

            # return success
            return {
                'responseCode': 200
            }, 200

        except exc.IntegrityError as e:
            db.session().rollback()
            # return error: vehicle already exists
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add vehicle: vehicle already exists!', 
                'responseCode': 400
            }, 400

        except exc.SQLAlchemyError as e:
            db.session().rollback()
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add vehicle: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add vehicle: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            db.session().rollback()
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add vehicle: unknown exception.', 
                'responseCode': 500
            }, 500


class ListVehicles(Resource):
    """
        API endpoint to list all existing vehicles.
    """

    def get(self):
        try:
            return {
                "vehicles": [
                    {
                        "vehicleNr": vehicle.vehicle_nr,
                        "vehicleType": vehicle.vehicle_type.value,
                        "ownerId": vehicle.owner_id
                    } for vehicle in Vehicle.query.all()
                ],
                'responseCode': 200
            }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles.', 
                'responseCode': 500
            }, 500


class DeleteVehicle(Resource):
    """
        API endpoint to delete a vehicle.
    """

    def delete(self, vehicle_nr:str):
        try:
            # retrieve vehicle data
            flag, status_code, vehicle_data = make_get_request('http://vehicles:5000/get/{}/'.format(vehicle_nr))

            # check if vehicle exists
            if not flag:
                # 400 => vehicle does not exists
                if status_code == 400:
                    return {
                        'causeErrorMessage': 'N/A',
                        'causeErrorStatus': -1,
                        'errorMessage': 'Cannot remove vehicle: vehicle does not exist.',
                        'responseCode': 400
                    }, 400

                else:
                    return {
                        'causeErrorMessage': vehicle_data['errorMessage'],
                        'causeErrorStatus': status_code,
                        'errorMessage': 'Cannot remove vehicle: unknown exception occurred while retrieving vehicle.', 
                        'responseCode': 500
                    }, 500

            # authenticate user
            if not 'username' in request.headers:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'username' entry in HTTP request header.",
                    'responseCode': 400
                }, 400

            if not 'password' in request.headers:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'password' entry in HTTP request header.",
                    'responseCode': 400
                }, 400

            # NOTE: this can cause a 400 error if this data is not present!
            username = request.headers['username']
            password = request.headers['password']

            # authenticate user
            flag, status_code, auth_data = make_get_request('http://users:5000/auth/', headers={'username': username, 'password': password})

            if not flag:
                # ERROR while authenticating user => "Cannot authenticate user"
                return {
                    'causeErrorMessage': auth_data['errorMessage'],
                    'causeErrorStatus': status_code,
                    'errorMessage': 'Error while authenticating user.',
                    'responseCode': 500
                }, 500
            elif not auth_data['result']:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Cannot authenticate user: ' + auth_data['reason'] + ' Please specify a valid username and password.',
                    'responseCode': 400
                }, 400

            # check if user is the owner of the vehicle
            if auth_data['userId'] != vehicle_data['ownerId']:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Cannot remove vehicle, specified user does not own the specified vehicle.',
                    'responseCode': 400
                }, 400

            # check if there are reviews that were not made by the owner
            flag, status_code, vehicle_review_data = make_get_request('http://vehiclereviews:5000/vehicle/{}/reviews/'.format(vehicle_nr))

            if flag:
                for review in vehicle_review_data['reviews']:
                    if review['reviewerId'] != vehicle_data['ownerId']:
                        return {
                            'causeErrorMessage': 'N/A',
                            'causeErrorStatus': -1,
                            'errorMessage': 'Cannot remove vehicle: other users have already reviewed the vehicle.',
                            'responseCode': 400
                        }, 400
            else:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Failed to retrieve vehicle reviews while trying to remove vehicle.',
                    'responseCode': 500
                }, 500

            delete_request_headers = {
                'username': username,
                'password': password
            }

            # delete vehicle
            flag, status_code, delete_result = make_delete_request('http://vehiclereviews:5000/vehicle/{}/reviews/delete/'.format(vehicle_nr), headers=request.headers)

            if not flag:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Failed to delete vehicle reviews while trying to remove vehicle.',
                    'responseCode': 500
                }, 500

            # do delete
            num_rows_deleted = Vehicle.query.filter_by(vehicle_nr=vehicle_nr).delete()

            # if any rows are deleted => success
            if num_rows_deleted > 0:
                db.session().commit()
                return {
                    'responseCode': 200
                }, 200

            # no rows are deleted => vehicle did not exist
            else:
                # NOTE: this code should never get executed since the vehicle will exist
                db.session().rollback()
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Cannot remove vehicle: vehicle does not exist.', 
                    'responseCode': 400
                }, 400

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            db.session().rollback()
            return {
                'causeErrorMessage': str(e),
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove vehicle: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove vehicle: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            db.session().rollback()
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove vehicle: unknown exception.', 
                'responseCode': 500
            }, 500


class GetVehicle(Resource):
    """
        API endpoint to retrieve information about a single vehicle.
    """

    def get(self, vehicle_nr):
        try:
            vehicle = Vehicle.query.filter_by(vehicle_nr=vehicle_nr).first()

            if vehicle is None:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Vehicle with specified vehicle id does not exist.',
                    'responseCode': 400
                }, 400

            else:
                return {
                    'vehicleNr': vehicle.vehicle_nr,
                    "vehicleType": vehicle.vehicle_type.value,
                    "ownerId": vehicle.owner_id,
                    'responseCode': 200,
                }, 200
        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle.', 
                'responseCode': 500
            }, 500


class ByOwner(Resource):
    """
        API endpoint to retrieve all vehicles owned by the specified user.
    """

    def get(self, owner_id):
        try:
            vehicles = Vehicle.query.filter_by(owner_id=owner_id).all()

            return {
                "vehicles": [ 
                    {
                        'vehicleNr': vehicle.vehicle_nr,
                        "vehicleType": vehicle.vehicle_type.value,
                    } for vehicle in vehicles
                ],
                'responseCode': 200,
            }, 200
        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles for specified user: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles for specified user: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicles for specified user: unknown exception.', 
                'responseCode': 500
            }, 500


api.add_resource(VehiclesHW, '/hello_world/')
api.add_resource(CreateVehicle, '/create/')
api.add_resource(ListVehicles, '/list/')
api.add_resource(DeleteVehicle, '/delete/<string:vehicle_nr>/')
api.add_resource(GetVehicle, '/get/<string:vehicle_nr>/')
api.add_resource(ByOwner, '/owner/<string:owner_id>/')
