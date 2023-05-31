#
#   Para explicación visitar: https://neo4j.com/developer/python-movie-app/
#
#   Para revisar el código de ejempl visitar: https://github.com/neo4j-examples/neo4j-movies-template en el apartado de flask-api
#

import os, ast

from flask import Flask, g, send_from_directory, request
from flask_cors import CORS
from flask_restful import Resource
from flask_restful_swagger_2 import Api, swagger, Schema
from flask_json import FlaskJSON, json_response

from dotenv import load_dotenv, find_dotenv

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

load_dotenv(find_dotenv())

app = Flask(__name__)

CORS(app)
FlaskJSON(app)

api = Api(app, title='Neo4j Anime project', api_version='0.0.1')


@api.representation('application/json')
def output_json(data, code, headers=None):
    return json_response(data_=data, headers_=headers, status_=code)


def env(key, default=None, required=True):
    """
    Retrieves environment variables and returns Python natives. The (optional)
    default will be returned if the environment variable does not exist.
    """
    try:
        value = os.environ[key]
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value
    except KeyError:
        if default or not required:
            return default
        raise RuntimeError("Missing required environment variable '%s'" % key)


DATABASE_USERNAME = env('ANIME_DATABASE_USERNAME')
DATABASE_PASSWORD = env('ANIME_DATABASE_PASSWORD')
DATABASE_URL = env('ANIME_DATABASE_URL')
# DATABASE_USERNAME = 'neo4j'
# DATABASE_PASSWORD = 'HolaPerro123'
# DATABASE_URL = 'neo4j+ssc://7eeebc6c.databases.neo4j.io'

if not DATABASE_USERNAME:
    print("Fallo")
    exit()
driver = GraphDatabase.driver(DATABASE_URL, auth=(DATABASE_USERNAME, str(DATABASE_PASSWORD)))

app.config['SECRET_KEY'] = env('SECRET_KEY')
# app.config['SECRET_KEY'] = 'SECRETO'


def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()


#---------------------------------------------
#
#   Conversores a JSON de los objetos de neo4j
#
#---------------------------------------------

def serialize_studio(studio):
    return {
        "StudioId": studio['StudioId'],
        "Name": studio['Name']
    }

def serialize_type(type):
    return {
        "TypeId": type['TypeId'],
        "Type": type['Type']
    }

def serialize_anime(anime):
    return {
        "AnimeID": anime['AnimeID'],
        "Name": anime['Name'],
        "Japanese_name": anime['Japanese_name'],
        "Episodes": anime['Episodes'],
        "Release_season": anime['Release_season'],
        "Tags": anime['Tags'],
        "Rating": anime['Rating'],
        "Release_year": anime['Release_year'],
        "Viewed": anime['Viewed']
    }

def serialize_full_anime(record):
    anime = record['a']
    tipo = record['t']
    studio = record['s']
    return {
        "AnimeID": anime['AnimeID'],
        "Name": anime['Name'],
        "Japanese_name": anime['Japanese_name'],
        "Episodes": anime['Episodes'],
        "Release_season": anime['Release_season'],
        "Tags": anime['Tags'],
        "Rating": anime['Rating'],
        "Release_year": anime['Release_year'],
        "Viewed": anime['Viewed'],
        "Type": tipo['Type'],
        "Studio": studio['Name']
    }


#-----------------------------------------------------------------------------------
#
#   Declaración de los modelos que detallan las etiquetas y propiedades de los nodos
#
#-----------------------------------------------------------------------------------

class AnimeModel(Schema):
    type = 'object'
    properties = {
        "AnimeID": {'type': 'integer'},
        "Name": {'type': 'string'},
        "Japanese_name": {'type': 'string'},
        "Episodes": {'type': 'integer'},
        "Release_season": {'type': 'string'},
        "Tags": {'type': 'string'},
        "Rating": {'type': 'double'},
        "Release_year": {'type': 'integer'},
        "Viewed": {'type': 'boolean'}
    }

class FullAnimeModel(Schema):
    type = 'object'
    properties = {
        "AnimeID": {'type': 'integer'},
        "Name": {'type': 'string'},
        "Japanese_name": {'type': 'string'},
        "Episodes": {'type': 'integer'},
        "Release_season": {'type': 'string'},
        "Tags": {'type': 'string'},
        "Rating": {'type': 'double'},
        "Release_year": {'type': 'integer'},
        "Viewed": {'type': 'boolean'},
        "Type": {'type': 'String'},
        "Studio": {'type': 'String'}
    }
    

class TypeModel(Schema):
    type = 'object'
    properties = {
        "TypeID": {'type': 'integer'},
        "Type": {'type': 'string'}
    }

class StudioModel(Schema):
    type = 'object'
    properties = {
        "StudioId": {'type': 'integer'},
        "Name": {'type': 'string'}
    }

#------------------------------------------------------------------
#
#   Declaración de clases que atenderán las peticiones al servidor
#
#------------------------------------------------------------------

class ApiDocs(Resource):
    def get(self, path=None):
        if not path:
            path = 'index.html'
        return send_from_directory('swaggerui', path)
    

class StudioList(Resource):
    @swagger.doc({
        'tags': ['Studio'],
        'summary': 'Find all studios',
        'description': 'Returns all studios',
        'responses': {
            '200': {
                'description': 'A list of studios',
                'schema': StudioModel,
            }
        }
    })
    def get(self):
        def get_studios(tx):
            return list(tx.run('MATCH (studio:Studio) RETURN studio'))
        db = get_db()
        result = db.write_transaction(get_studios)
        return [serialize_studio(record['studio']) for record in result]


class TypeList(Resource):
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Find all types',
        'description': 'Returns all types',
        'responses': {
            '200': {
                'description': 'A list of types',
                'schema': TypeModel,
            }
        }
    })
    def get(self):
        def get_types(tx):
            return list(tx.run('MATCH (type:Type) RETURN type'))
        db = get_db()
        result = db.write_transaction(get_types)
        return [serialize_type(record['type']) for record in result]

class AnimeList(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find all Animes',
        'description': 'Returns all animes',
        'responses': {
            '200': {
                'description': 'A list of animes',
                'schema': TypeModel,
            }
        }
    })
    def get(self):
        def get_animes(tx):
            return list(tx.run('MATCH (anime:Anime) RETURN anime'))
        db = get_db()
        result = db.write_transaction(get_animes)
        print(result[0])
        return [serialize_anime(record['anime']) for record in result]

class FullAnimeList(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find all Animes',
        'description': 'Returns all animes',
        'responses': {
            '200': {
                'description': 'A list of animes',
                'schema': TypeModel,
            }
        }
    })
    def get(self):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a, t, s"))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]
    
    def post(self):
        data = request.get_json()
        name = data.get('username')
        japanese_name = data.get('password')
        episodes = data.get('episodes')
        release_season = data.get('release_season')
        tags = data.get('tags')
        rating = data.get('rating')
        release_year = data.get('release_year')

        tipo = data.get('type')
        studio = data.get('studio')
        
        if not name:
            return {'name': 'This field is required.'}, 400
        if not tipo:
            return {'type': 'This field is required.'}, 400
        if not studio:
            return {'studio': 'This field is required.'}, 400
        
        def get_animes_by_name(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(a.Name) = toLower('" + name + "') or toLower(a.Japanese_name) = toLower('" + japanese_name + "') return a, t, s"
            return tx.run(cypher_query).single()
        
        db = get_db()
        result = db.begin_transaction(get_animes_by_name)
        if result and result[0]:
            return {'error': 'Anime name is already registered'}, 400
        
        def create_anime(tx):
            cypher_query = '''
                match (animes:Anime)
                with  count(animes)+1 as id
                match (t:Type{TypeId: $typeId})
                match (s:Studio{StudioId: $studioId})
                merge (a:Anime{AnimeID: id, Name: $name, Japanese_name: $japanese_name, Episodes: $episodes, Release_season: $release_season, Tags: $tags, Rating: $rating, Release_year: $release_year, Viewed: False})
                merge (a)-[:TRANSMITTED_IN]->(t)
                merge (s)-[:PRODUCED]->(a)
                return a
            '''
            return list(tx.run(cypher_query, {
                'name': name,
                'japanese_name': japanese_name,
                'episodes': episodes,
                'release_season': release_season,
                'tags': tags,
                'rating': rating,
                'release_year': release_year,
                'typeId': tipo,
                'studioId': studio
            }))
        
        results = db.write_transaction(create_user, username, password)
        anime = results['a']
        return serialize_anime(anime), 201
        



class AnimeListByStudio(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find all Animes produced by an specific studio',
        'description': 'Returns all animes poduced by an studio',
        'responses': {
            '200': {
                'description': 'A list of animes produced by an studio',
                'schema': TypeModel,
            }
        }
    })
    def get(self, studio_name):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(s.Name) contains toLower('" + studio_name + "') return a, t, s"
            return list(tx.run(cypher_query))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]

class AnimeListByName(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find all Animes whith an especific name',
        'description': 'Returns all animes with a name',
        'responses': {
            '200': {
                'description': 'A list of animes with a name',
                'schema': TypeModel,
            }
        }
    })
    def get(self, anime_name):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(a.Name) contains toLower('" +anime_name + "') or toLower(a.Japanese_name) contains toLower('" +anime_name + "') return a, t, s"
            return list(tx.run(cypher_query))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]


#-------------------------------------
#
#   Creando los endpoints del REST API
#
#-------------------------------------


api.add_resource(ApiDocs, '/api/v0/docs')
api.add_resource(StudioList, '/api/v0/studios')
api.add_resource(TypeList, '/api/v0/types')
api.add_resource(FullAnimeList, '/api/v0/animes')
api.add_resource(AnimeListByName, '/api/v0/animes/by_name/<string:anime_name>')
api.add_resource(AnimeListByStudio, '/api/v0/animes/by_studio/<string:studio_name>')
# @app.route('/ping')
# def ping():
#     return jsonify({'message': 'Pong!'})

# @app.route('/products')
# def get_products():
#     return jsonify(products)

# @app.route('/products/<string:product_name>')
# def get_product_by_name(product_name):
#     founded = [product for product in products if product['name'] == product_name]
#     if len(founded) > 0: 
#         return jsonify(founded[0])
#     else:
#         # return jsonify({'message', 'Product not found'})
#         return "Not Found", 404

# @app.route('/products', methods=['POST'])
# def post_product():
#     new_product = {
#         "name": request.json['name'],
#         "price": request.json['price'],
#         'quantity': int(request.json['quantity'])
#     }
#     products.append(new_product)
#     return jsonify(products)

# if __name__ == "__main__":
#     app.run(debug=True, port=4000)