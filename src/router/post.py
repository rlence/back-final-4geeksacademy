from flask import request, jsonify

def post_route(app, token_required):

    @app.route('/post/route', methods=['POST'])
    @token_required
    def post_test():
        print('hola')
        return jsonify('haciendo prueba'), 200

