from flask import Flask, render_template, Response, flash, jsonify, abort
import json
import requests
import sys
import os

app = Flask(__name__, template_folder='./templates/')

app_settings = os.getenv('APP_SETTINGS')
app.config.from_object(app_settings)

@app.errorhandler(404)
def error_404(error):
    return render_template('error_page.html', error_code = 404, message=str(error))

@app.errorhandler(500)
def error_500(error):
    return render_template('error_page.html', error_code = 500, message=str(error))

# Flash categories:
#   error, warning, success

def make_get_request(url:str, **kwargs) -> (bool, dict):
    """
        Send a GET request to the specified URL with the specified arguments. 

        The return value is a tuple (bool, status, data). 'bool' will be true in case the call returns code 200, False otherwise.
        'status' contains the HTTP status code of the response. 'data' contains the reponse data, or error data in case of an error.
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
    """

    print("Making call to '{}'...".format(url))
    resp = requests.post(url, data=post_params, **kwargs)
    print("Received response.")

    if not resp.ok:
        return False, resp.status_code, json.loads(resp.content)

    return True, resp.status_code, json.loads(resp.content)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/users/', methods=["GET", "POST"])
def users_overview():

    # retrieve list of users
    flag, status_code, data = make_get_request('http://users:5000/list/')

    if not flag:
        flash(message=data['errorMessage'], category="error")
        users = []
    else:
        users = data["users"]

    return render_template('users_overview.html', users=users)


@app.route('/users/<int:user_id>/', methods=["GET"])
def users_details(user_id):

    # retrieve user information
    flag, status_code, data = make_get_request('http://users:5000/get/{}/'.format(user_id))

    if flag:
        user = data
    else:
        if status_code == 400: # invalid request => invalid user id
            abort(404, "Cannot find user: invalid user id.")
        else:
            abort(500, "Error while retrieving user: internal error.")

    # retrieve vehicle data and map vehicle nrs to vehicle data
    flag, status_code, vehicle_data = make_get_request('http://vehicles:5000/list/')

    if not flag:
        abort(500, "Error while retrieving vehicle information.")

    # create dict that maps vehicle id's to vehicle info
    vehicle_map = {
        vehicle['vehicleNr']: {
            'vehicleType': vehicle['vehicleType'],
        } for vehicle in vehicle_data["vehicles"]
    }

    # retrieve vehicle reviews made by the user
    flag, status_code, vehicle_review_data = make_get_request('http://vehiclereviews:5000/reviewer/{}/reviews/'.format(user_id))

    if flag:
        vehicle_reviews = [
            {
                'score': review['score'],
                'vehicleNr': review['vehicleNr'],
                'vehicleType': vehicle_map[review['vehicleNr']]['vehicleType'],
            } for review in vehicle_review_data['reviews']
        ]
    else:
        abort(500, "Error while retrieving vehicle reviews.")

    # retrieve stop reviews made by the user
    flag, status_code, stop_review_data = make_get_request('http://stopreviews:5000/reviewer/{}/reviews/'.format(user_id))

    if flag:
        stop_reviews = [
            {
                'stopId': review['stopId'],
                'score': review['score']
            } for review in stop_review_data['reviews']
        ]
    else:
        abort(500, "Error while retrieving stop reviews.")

    # retrieve information about the owner
    flag, status_code, vehicle_data = make_get_request('http://vehicles:5000/owner/{}/'.format(user_id))

    if flag:
        vehicles=vehicle_data["vehicles"]
    else:
        flash(message="Cannot retrieve vehicles owned by user: '" + vehicle_data['errorMessage'] + "'.", category="error")
        vehicles=[]

    return render_template('users_details.html', user=user, vehicle_reviews=vehicle_reviews, stop_reviews=stop_reviews, vehicles=vehicles)


@app.route('/vehicles/', methods=["GET", "POST", "DELETE"])
def vehicles_overview():

    # retrieve list of vehicles
    flag, status_code, vehicle_data = make_get_request('http://vehicles:5000/list/')

    if not flag:
        flash(message=vehicle_data['errorMessage'], category="error")
        vehicles = []
        return render_template('vehicles_overview.html', vehicles=vehicles)

    # retrieve user data and map user id's to user data
    flag, status_code, user_data = make_get_request('http://users:5000/list/')

    if not flag:
        flash(message=user_data['errorMessage'], category="error")
        vehicles = []
        return render_template('vehicles_overview.html', vehicles=vehicles)

    # create dict that maps user id's to user info.
    user_map = {
        user['id']: {
            'username': user['username'],
            'email': user['email']
        } for user in user_data["users"]
    }

    # create list of vehicles
    vehicles = [
        {
            "vehicleNr": vehicle['vehicleNr'],
            "vehicleType": vehicle['vehicleType'],
            "owner": user_map[vehicle['ownerId']]
        } for vehicle in vehicle_data["vehicles"]
    ]

    return render_template('vehicles_overview.html', vehicles=vehicles)


@app.route('/vehicles/<int:vehicle_nr>/')
def vehicles_details(vehicle_nr):

    # retrieve vehicle
    flag, status_code, vehicle_data = make_get_request('http://vehicles:5000/get/{}/'.format(vehicle_nr))

    if flag:
        vehicle = vehicle_data
    else:
        if status_code == 400: # invalid request => invalid vehicle nr
            abort(404, "Cannot find vehicle: invalid vehicle number.")
        else:
            abort(500, "Cannot find vehicle: internal server error.")

    # retrieve user data and map user id's to user data
    flag, status_code, user_data = make_get_request('http://users:5000/list/')

    if not flag:
        abort(500, "Error while retrieving reviewer information.")

    user_map = {
        user['id']: {
            'username': user['username'],
            'email': user['email']
        } for user in user_data["users"]
    }

    # retrieve vehicle ratings
    flag, status_code, vehicle_review_data = make_get_request('http://vehiclereviews:5000/vehicle/{}/reviews/'.format(vehicle_nr))

    if flag:
        # create list of reviews by mapping reviewer user id to user data
        reviews = [
            {
                "userId":   review['reviewerId'],
                "username": user_map[review['reviewerId']]['username'],
                "email":    user_map[review['reviewerId']]['email'],
                "score":    review['score']
            } for review in vehicle_review_data['reviews']
        ]
    else:
        abort(500, "Error while retrieving vehicle reviews.")

    # retrieve vehicle score
    flag, status_code, score_data = make_get_request('http://vehiclereviews:5000/vehicle/{}/score/'.format(vehicle_nr))

    # set average rating
    if flag:
        vehicle['rating'] = score_data['score']
    else:
        if status_code == 400:
            vehicle['rating'] = "N/A"
        else:
            abort(500, "Error while retrieving vehicle score.")

    # get owner info
    flag, status_code, owner_data = make_get_request('http://users:5000/get/{}/'.format(vehicle['ownerId']))

    if flag:
        owner = owner_data
    else:
        if status_code == 400:
            abort(500, "Cannot retrieve owner: owner does not exist.")
        else:
            abort(500, "Cannot retrieve owner: internal error.")

    return render_template('vehicles_details.html', owner=owner, vehicle=vehicle, reviews=reviews)


@app.route('/stops/', defaults={'province_id':0, 'line_id':0, 'city_id':0, 'filter_policy': "NONE"})
@app.route('/stops/provinces/<int:province_id>/', defaults={'line_id':0, 'city_id':0, 'filter_policy': "PROVINCE"})
@app.route('/stops/provinces/<int:province_id>/lines/<int:line_id>/', defaults={'city_id':0, 'filter_policy': "LINE"})
@app.route('/stops/cities/<int:city_id>/', defaults={'province_id':0, 'line_id':0, 'filter_policy': "CITY"})
def stops_overview(province_id, line_id, city_id, filter_policy):
    
    # retrieve list of provinces
    flag, status_code, data_provinces = make_get_request("http://stops:5000/provinces/")

    if not flag:
        abort(500, "Error while retrieving provinces.")

    provinces = data_provinces["provinces"]

    # retrieve list of cities
    flag, status_code, data_cities = make_get_request("http://stops:5000/cities/")

    if not flag:
        abort(500, "Error while retrieving cities.")

    cities = data_cities['cities']

    if filter_policy == "NONE":
        # default is empty
        return render_template('stops_overview.html', stops=[], provinces=provinces, cities=cities)

    elif filter_policy == "PROVINCE":
        url_stops = "http://stops:5000/provinces/{}/stops/".format(province_id)

    elif filter_policy == "LINE":
        url_stops = "http://stops:5000/provinces/{}/lines/{}/stops/".format(province_id, line_id)

    elif filter_policy == "CITY":
        url_stops = "http://stops:5000/cities/{}/stops/".format(city_id)

    # retrieve list of stops
    flag, status_code, data_stops = make_get_request(url_stops)

    if not flag:
        abort(500, "Error while retrieving stops.")

    stops = data_stops['stops']

    return render_template('stops_overview.html', stops=stops, provinces=provinces, cities=cities)


@app.route('/stops/<int:stop_id>/', methods=["GET", "POST"])
def stops_details(stop_id):

    # retrieve user data and map user id's to user data
    flag, status_code, user_data = make_get_request('http://users:5000/list/')

    if not flag:
        abort(500, "Error while retrieving reviewer information.")

    user_map = {
        user['id']: {
            'username': user['username'],
            'email': user['email']
        } for user in user_data["users"]
    }

    # retrieve stop ratings
    flag, status_code, vehicle_review_data = make_get_request('http://stopreviews:5000/stop/{}/reviews/'.format(stop_id))

    if flag:
        # create list of reviews by mapping reviewer user id to user data
        reviews = [
            {
                "userId":   review['reviewerId'],
                "username": user_map[review['reviewerId']]['username'],
                "email":    user_map[review['reviewerId']]['email'],
                "score":    review['score']
            } for review in vehicle_review_data['reviews']
        ]
    else:
        abort(500, "Error while retrieving reviews.")

    flag, status_code, score_data = make_get_request('http://stopreviews:5000/stop/{}/score/'.format(stop_id))

    stop = {
        'stopId': stop_id
    }

    # set average rating
    if flag:
        stop['score'] = score_data['score']
    else:
        if status_code == 400:
            stop['score'] = "N/A"
        else:
            abort(500, "Error while retrieving stop score.")

    return render_template('stops_details.html', stop=stop, reviews=reviews)

