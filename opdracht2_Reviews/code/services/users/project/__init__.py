import sys
import os

from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from passlib.hash import sha256_crypt

############### FLASK INIT & CONFIG ###############

app = Flask(__name__)

app_settings = os.getenv('APP_SETTINGS')
app.config.from_object(app_settings)

############### DB SETTINGS ###############

# init DB
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"

    id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    email    = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return "<User id={}, username={}, email={}, password={}>".format(self.id, self.username, self.email, self.password)

############### API ###############

api = Api(app)


class UsersHW(Resource):
    """
        Hello-world API endpoint
    """

    def get(self):
        return {
            'responseCode': 200,
            'message': 'Hello world!'
        }, 200


class CreateUser(Resource):
    """
        API call for creating users.
    """

    def post(self):
        # get params

        try:
            # verify input
            if not 'username' in request.form:
                # username not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'username' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            if not 'email' in request.form:
                # email not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'email' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            if not 'password' in request.form:
                # password not in form
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': "Missing 'password' entry in HTTP request body.",
                    'responseCode': 400
                }, 400

            username = request.form["username"]
            email    = request.form["email"]
            password = sha256_crypt.hash(request.form["password"])

            # add to DB
            new_user = User(username=username, email=email, password=password)

            db.session.add(new_user)
            db.session.commit()

            # return success
            return {
                'responseCode': 200
            }, 200

        except exc.IntegrityError as e:
            db.session().rollback()
            # return error
            return {
                'causeErrorMessage': str(e), 
                'errorMessage': 'Cannot add user: user already exists!', 
                'responseCode': 400
            }, 400

        except exc.SQLAlchemyError as e:
            db.session().rollback()
            # return error
            return {
                'causeErrorMessage': str(e), 
                'errorMessage': 'Cannot add user: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot add user: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            db.session().rollback()
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'errorMessage': 'Cannot add user: unknown exception.', 
                'responseCode': 500
            }, 500


class AuthUser(Resource):
    """
        API call for authenticating users.
    """
    
    def get(self):

        try:
            username = request.headers['username']
            password = request.headers['password']

            user = User.query.filter_by(username=username).first()
            
            if user is None:
                return {
                    'userId': -1,
                    'result': False,
                    'reason': 'Username does not exist.',
                    'responseCode': 200
                }, 200
            else:
                password_ok = sha256_crypt.verify(password, user.password)

                if password_ok:
                    return {
                        'userId': user.id,
                        'result': True,
                        'reason': 'N/A',
                        'responseCode': 200
                    }, 200

                else:
                    return {
                        'userId': -1,
                        'result': False,
                        'reason': 'Invalid password.',
                        'responseCode': 200
                    }, 200

        except exc.SQLAlchemyError as e:
            db.session().rollback()
            # return error
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot verify user: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot verify user: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot verify user: unknown exception.',
                'responseCode': 500
            }, 500


class ListUsers(Resource):
    """
        API call for retrieving a list of all users present in the system.
        Only the id, username, and email address will be included in the list.
    """

    def get(self):

        try:        
            return {
                "users": [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    } for user in User.query.all()
                ]
            }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve users: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve users: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve users.', 
                'responseCode': 500
            }, 500


class GetUser(Resource):
    """
        API call for retrieve information about one single user.
    """

    def get(self, user_id:int):

        try:
            user = User.query.filter_by(id=user_id).first()

            if user is None:
                return {
                    'causeErrorMessage': 'N/A',
                    'causeErrorStatus': -1,
                    'errorMessage': 'User with specified user id does not exist.',
                    'responseCode': 400
                }, 400

            else:
                return {
                    'username': user.username,
                    'email': user.email,
                    'id': user.id,
                    'responseCode': 200,
                }, 200

        except exc.SQLAlchemyError as e:
            # return error: something went wrong in the database
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve user: unknown SQLA exception.', 
                'responseCode': 500
            }, 500

        except Exception as e:
            db.session().rollback()
            # return error: python exception
            return {
                'causeErrorMessage': str(e), 
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve user: unknown Python exception.', 
                'responseCode': 500
            }, 500

        except:
            # return error
            return {
                'causeErrorMessage': 'N/A',
                'causeErrorStatus': -1,
                'errorMessage': 'Cannot retrieve user.', 
                'responseCode': 500
            }, 500


api.add_resource(UsersHW, '/hello_world/')
api.add_resource(CreateUser, '/create/')
api.add_resource(AuthUser, '/auth/')
api.add_resource(ListUsers, '/list/')
api.add_resource(GetUser, '/get/<int:user_id>/')
