from flask import Flask, g
from flask_cors import CORS
from flask_json import FlaskJSON, json_response

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

# @app.response_class('application/json')
# def output_json(data, code, headers=None):
#     return json_response(data_=data, headers_=headers, status_=code)

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


@app.route('/', methods=['GET'])
def index():
    return '''
        <h1>Hola si funciona esto!</h1>
    '''

if __name__ == "__main__":
    app.run(host='0.0.0.0')
