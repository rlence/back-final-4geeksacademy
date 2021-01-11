import bcrypt

#password = "secret_pasword"

def encrypted_pass(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))
    return hashed

def compare_pass(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)