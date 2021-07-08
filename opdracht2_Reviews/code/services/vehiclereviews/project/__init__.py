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

    if not resp.ok:
        return False, resp.status_code, json.loads(resp.content)

    return True, resp.status_code, json.loads(resp.content)


def make_post_request(url:str, post_params:dict, **kwargs):
    """
        Send a POST request to the specified URL with the specified arguments. The 'post_params' argument is
        a dict that contains (key, value) pairs which will be sent as form data. All other keyword arguments will be passed to the requests library.

        The return value is a tuple (bool, status, data). 'bool' will be true in case the call returns code 200, False otherwise.
        'status' contains the HTTP status code of the response. 'data' contains the reponse data, or error data in case of an error.

        Note: 'headers' parameter contains a dict with header data.
    """

    print("Making call to '{}'...".format(url))
    resp = requests.post(url, data=post_params, **kwargs)
    print("Received response.")

    if not resp.ok:
        return False, resp.status_code, json.loads(resp.content)

    return True, resp.status_code, json.loads(resp.content)

############### DB SETTINGS ###############

# init DB
db = SQLAlchemy(app)

class VehicleReview(db.Model):
    __tablename__ = "vehiclereviews"

    vehicle_nr  = db.Column(db.String(50), nullable=False, primary_key=True)
    reviewer_id = db.Column(db.Integer,    nullable=False, primary_key=True)
    score       = db.Column(db.Float,      nullable=False)

    def __repr__(self):
        return "<VehicleReview id={}, vehicle_nr={}, reviewer_id={}, rating={}>".format(self.id, self.vehicle_nr, self.reviewer_id, self.rating)

############### API ###############

api = Api(app)


class VehicleReviewsHW(Resource):
    """
        Hello-world API endpoint
    """

    def get(self):
        return {
            'responseCode': 200,
            'message': 'Hello world!'
        }, 200


class CreateReview(Resource):
    """
        API entrypoint to create vehicle review.
    """
    
    def post(self):
        try:
            # authenticate user: False => 400
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

            # check if form is ok
            if not 'vehicleNr' in request.form:
                # vehicleNr not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'vehicleNr' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            if not 'score' in request.form:
                # score not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'score' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            vehicle_nr    = request.form["vehicleNr"]
            vehicle_score = request.form['score']

            # place in DB
            new_review = VehicleReview(vehicle_nr=vehicle_nr, reviewer_id=auth_data['userId'], score=vehicle_score)

            db.session.add(new_review)
            db.session.commit()

            # return success
            return {
                'responseCode': 200
            }, 200

        except exc.IntegrityError as e:
            db.session().rollback()
            # return error: review already exists
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add review: review for specified user and vehicle already exists!', 
                'responseCode': 400
            }, 400

        except exc.SQLAlchemyError as e:
            db.session().rollback()
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add review: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add review: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            db.session().rollback()
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add review: unknown exception.', 
                'responseCode': 500
            }, 500


class GetScore(Resource):
    """
        API entrypoint to retrieve the average score of a vehicle.
    """

    def get(self, vehicle_nr):
        try:
            reviews = VehicleReview.query.filter_by(vehicle_nr=vehicle_nr).all()

            if len(reviews) == 0:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'Specified vehicle does not have any reviews.', 
                    'responseCode': 400
                }, 400

            score = sum([review.score for review in reviews]) / len(reviews)

            return {
                'score': score,
                "responseCode": 200
            }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score.', 
                'responseCode': 500
            }, 500


class GetReviewsForReviewer(Resource):
    """
        API entrypoint to retrieve all reviews made by the specified user.
    """
    
    def get(self, user_id):
        try:
            reviews = VehicleReview.query.filter_by(reviewer_id=user_id).all()

            return {
                "reviews": [
                    {
                        "vehicleNr": review.vehicle_nr,
                        "reviewerId": review.reviewer_id,
                        "score":     review.score
                    } for review in reviews
                ],
                "responseCode": 200
            }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve vehicle score.', 
                'responseCode': 500
            }, 500


class GetReviewsForVehicle(Resource):
    """
        API entrypoint to retrieve all reviews made for the specified vehicle.
    """

    def get(self, vehicle_nr):
        try:
            reviews = VehicleReview.query.filter_by(vehicle_nr=vehicle_nr).all()

            return {
                "reviews": [
                    {
                        "vehicleNr": review.vehicle_nr,
                        "reviewerId": review.reviewer_id,
                        "score":     review.score
                    } for review in reviews
                ],
                "responseCode": 200
            }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve reviews: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve reviews: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve reviews.', 
                'responseCode': 500
            }, 500


class DeleteReviewsForVehicle(Resource):
    """
        API entrypoint to delete all reviews for the specified vehicle.

        This will remove all reviews with the specified vehicle_nr.
    """

    def delete(self, vehicle_nr):
        try:
            # authenticate user: False => 400
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

            # remove reviews
            num_rows_deleted = VehicleReview.query.filter_by(vehicle_nr=vehicle_nr).delete()

            # if any rows are deleted => success
            if num_rows_deleted > 0:
                db.session().commit()

            # no rows are deleted => success
            else:
                db.session().rollback()

            return {
                'responseCode': 200
            }, 200

        except exc.SQLAlchemyError as e:
            db.session().rollback()
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove review: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove review: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            db.session().rollback()
            # return error: something else went wrong
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot remove review: unknown exception.', 
                'responseCode': 500
            }, 500


api.add_resource(VehicleReviewsHW, '/hello_world/')
api.add_resource(CreateReview, '/create/')
api.add_resource(GetScore, '/vehicle/<string:vehicle_nr>/score/')
api.add_resource(GetReviewsForReviewer, '/reviewer/<int:user_id>/reviews/')
api.add_resource(GetReviewsForVehicle, '/vehicle/<string:vehicle_nr>/reviews/')
api.add_resource(DeleteReviewsForVehicle, '/vehicle/<string:vehicle_nr>/reviews/delete/')
