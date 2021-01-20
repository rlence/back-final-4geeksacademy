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
from models import db, User, Post, Comment
from encrypted import encrypted_pass, compare_pass

from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

from jwt_auth import encode_token, decode_token
import jwt

from router.post import post_route

from functools import wraps

#from models import Person

app = Flask(__name__, static_folder="./img")
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasuperkey'
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
HOST = 'https://3000-c490dbbd-2fff-4615-9811-dd7b8cd75bc8.ws-eu03.gitpod.io/'


#decorador
def token_required(f):
    @wraps(f)
    def decorador(*args , **kwargs ):
        try:
            auth = request.headers.get('Authorization')
            if auth is None:
                return jsonify("no token"), 403
            token = auth.split(' ')
            data = decode_token(token[1], app.config['SECRET_KEY'] )
            user = User.query.get(data['user']['id'])
            if user is None:
                return jsonify("no authorization"), 401

        except OSError as err:
            print(err)
            return jsonify("no authorization"), 401

        except jwt.exceptions.ExpiredSignatureError as err:
            print(err)
            return jsonify("expired token"), 403

        return f(*args , **kwargs)
    return decorador

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
    return  send_file("./img/" + filename)

post = post_route(app, token_required)

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

    auth = request.authorization
    print(auth)

    body = request.get_json()
    user = User.query.filter_by(email=body['email']).first()
    if(user is None):
        return "user not exist", 401
    is_validate = compare_pass(body['password'], user.password_bcrypt())
    if(is_validate == False):
        return "password incorrect", 401

    token = encode_token( user.serialize() , app.config['SECRET_KEY'])
    print(token)
    return jsonify({ "acces_token":token}), 200


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

@app.route('/post', methods=['GET'])
@token_required
def get_all_post():
    all_post = db.session.query(Post, User).join(User).all()
    new_all_post = []

    for post in all_post:
        new_obj = {
            "post":post[0].serialize(),
            "user":post[1].serialize()
        }
        new_all_post.append(new_obj)
        
    return jsonify(new_all_post), 200


@app.route('/post/<int:id>', methods=['GET'])
def get_my_post(id):

    print(id)
    my_post = Post.query.filter_by(user_id=id).all()
    print(my_post)
    all_post = []
    for post in my_post:
        all_post.append(post.serialize())

    return jsonify(all_post), 200

@app.route('/post/<int:id>', methods=['DELETE'])
def delete_post(id):
    print(id)
    post = Post.query.get(id)
    db.session.delete(post)
    db.session.commit()
    print(post)
    return jsonify('post borrado'), 200



# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
