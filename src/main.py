"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from os.path import join, dirname, realpath
from flask import Flask, request, jsonify, url_for, send_from_directory, send_file
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Post
from encrypted import encrypted_pass, compare_pass

from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

#from models import Person

app = Flask(__name__, static_folder="./img")
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
HOST = 'https://3000-d4ff11bd-ce8e-4f2e-9639-7fa4dbf90e0d.ws-eu03.gitpod.io/'

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

#send img
@app.route('/<filename>', methods=['GET'])
def send_img(filename):
    print(filename)
    path = os.path.join('./src/img')
    print(path)
    return  send_file("./img/" + filename)

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


@app.route('/post', methods=['POST'])
def create_post():

    data = dict(request.form)
    
    f = request.files['file']
    filename = secure_filename(f.filename)
    f.save(os.path.join('./src/img',filename))
    img_url = HOST + filename
    new_post = Post(img_url, data['text'], data['user_id'])
    db.session.add(new_post)
    db.session.commit()
    return jsonify(new_post.serialize()), 201


@app.route('/post/<id>', methods=['GET'])
def get_my_post(id):
    all_post = Post.query.filter_by(user_id = id).all()
    list_post = []
    for post in all_post:
        list_post.append(post.serialize())
    print(all_post)
    return jsonify(list_post), 200

@app.route('/post', methods=['GET'])
def all_post():
    all_post = db.session.query(Post, User).join(Post).all()
    return jsonify('todo los post'), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
