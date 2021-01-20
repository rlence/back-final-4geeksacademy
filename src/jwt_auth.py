import jwt
import datetime

def encode_token(user, key):
    print(user)
    print(key)
    return jwt.encode({"user":user, "exp":datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, key )

def decode_token(token, key):
    return jwt.decode(token, key, algorithms="HS256")