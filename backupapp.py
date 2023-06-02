from flask import Flask, g
from flask_restful import Api
from flask_cors import CORS
from flask_json import FlaskJSON, json_response
from controller.AnimeControllers import AnimeListByName, AnimeListByReleaseYear, AnimeListByStudio, AnimesById, FullAnimeList

from controller.StudioControllers import StudioById, StudioList
from controller.TypeControllers import TypeList, TypesById 

from tools.driver import env

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

api = Api(app)

@api.representation('application/json')
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


app.config['SECRET_KEY'] = env('SECRET_KEY')
# app.config['SECRET_KEY'] = 'SECRETO'


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


#-------------------------------------
#
#   Creando los endpoints del REST API
#
#-------------------------------------

# Studios Endpoints
api.add_resource(StudioList,            '/api/v0/studios')
api.add_resource(StudioById,            '/api/v0/studios/<int:studioId>')

# Types Endpoints
api.add_resource(TypeList,              '/api/v0/types')
api.add_resource(TypesById,             '/api/v0/types/<int:typeId>')

# Anime Endpoints
api.add_resource(FullAnimeList,         '/api/v0/animes')
api.add_resource(AnimeListByName,       '/api/v0/animes/by_name/<string:anime_name>')
api.add_resource(AnimeListByStudio,     '/api/v0/animes/by_studio/<string:studio_name>')
api.add_resource(AnimeListByReleaseYear,'/api/v0/animes/by_release_year/<int:release_year>')
api.add_resource(AnimesById,            '/api/v0/animes/by_id/<int:animeId>')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
