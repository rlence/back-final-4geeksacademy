"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
from encrypted import encrypted_pass, compare_pass
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user/register', methods=['POST'])
def register_user():
    try:

        body = request.get_json()
        if(body['email'] == '' or body['email'] == None):
            return jsonify({ "msg":"Email is not send"}), 400

        if(body['password'] == '' or body['password'] == None ):
            return jsonify({ "msg":"Password is not send"}), 400

        new_pass = encrypted_pass(body['password'])
        new_user = User(body['email'], new_pass)
        db.session.add(new_user)
        db.session.commit()
        print(new_user)
        response_body = {
            "msg": new_user.serialize()
        }
        return jsonify(response_body), 201

    except:
        response_body = {
            "msg":"User exist"
        }
        return jsonify(response_body), 400

@app.route('/user/login', methods=['POST'])
def login_user():

    body = request.get_json()
    print(body)
    user = User.query.filter_by(email=body['email']).first()
    if(user is None):
        return "user not exist", 401
    print(user)
    is_validate = compare_pass(body['password'], user.password_bcrypt())
    print(is_validate)
    if(is_validate == False):
        return "password incorrect", 401
    return jsonify("user login"), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
