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
    
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Create new Type',
        'description': 'Allow to create new types',
        'responses': {
            '201': {
                'description': 'New node created',
                'schema': TypeModel,
            },
            '400': {
                'description': 'The Type is already in the data base',
                'schema': TypeModel,
            },
            '500': {
                'description': 'No JSON data has been received in the body of the request or is bad formated',
                'schema': TypeModel,
            }
        }
    })
    def post(self):
        data = request.get_json()

        name = data.get('name')
        if not name:
            return {'name': 'This field is required.'}, 400

        def get_studio_by_name(tx, name):
            return tx.run(
                '''
                MATCH (studio:Studio)
                WHERE toLower(studio.Name) = toLower($name)
                RETURN studio
                ''', {'name': name}
            ).single()

        db = get_db()
        result = db.read_transaction(get_studio_by_name, name)
        if result and result.get('studio'):
            return {'studio': 'Studio is already in the data base'}, 400

        def create_studio(tx, name):
            return tx.run(
                '''
                MATCH (studios: Studio)
                WITH count(studios)+1 as id
                CREATE (studio:Type {StudioId: id, Name: $name})
                RETURN studio
                ''',
                {
                    'name': name
                }
            ).single()

        results = db.write_transaction(create_studio, name)
        tipo = results['studio']
        return serialize_type(tipo), 201


class StudioById(Resource):
    @swagger.doc({
        'tags': ['Studio'],
        'summary': 'Find an Studio',
        'description': 'Returns an Studio',
        'responses': {
            '200': {
                'description': 'Whole data of an Studio',
                'schema': StudioModel,
            }
        }
    })
    def get(self, studioId):
        def get_studio_by_id(tx, studioId):
            return tx.run(
                '''
                MERGE (studio:Studio {StudioId: $studioId})
                RETURN studio
                ''',
                {
                    "studioId": studioId
                }
            ).single()
        db = get_db()
        result = db.write_transaction(get_studio_by_id, studioId)
        return serialize_studio(result['studio']), 200
    
    @swagger.doc({
        'tags': ['Studio'],
        'summary': 'Update a Studio',
        'description': 'update the information of a Studio',
        'responses': {
            '200': {
                'description': 'Studio information updated',
                'schema': StudioModel,
            },
            '400': {
                'description': 'Bad request',
                'schema': StudioModel,
            },
            '500': {
                'description': 'No JSON data has been received in the body of the request or it is bad formated',
                'schema': StudioModel,
            }
        }
    })
    def put(self, studioId):
        data = request.get_json()
        # typeId = data.get('typeId')
        name = data.get('name')
        def update_studio(tx, studioId, name):
            return tx.run(
                '''
                MATCH (s:Studio {StudioId: $studioId})
                SET s.Name = $name
                RETURN s
                ''',
                {
                    'studioId': studioId,
                    'name': name
                }
            )
        db = get_db()
        result = db.write_transaction(update_studio, studioId, name)
        return serialize_studio(result['s']), 200
    
    @swagger.doc({
        'tags': ['Studio'],
        'summary': 'Delete a studio',
        'description': 'Delete the information of an sudio',
        'responses': {
            '200': {
                'description': 'Studio information deleted',
                'schema': StudioModel,
            },
            '400': {
                'description': 'Bad request',
                'schema': StudioModel,
            }
        }
    })
    def delete(self, studioId):
        def update_studio(tx, studioId):
            return tx.run(
                '''
                MATCH (s:Studio {StudioId: $studioId})
                DELETE s
                ''',
                {
                    'studioId': studioId,
                }
            )
        db = get_db()
        result = db.write_transaction(update_studio, studioId)
        return {'message': 'Node deleted with id '+ studioId}, 200


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
    
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Create new Type',
        'description': 'Allow to create new types',
        'responses': {
            '201': {
                'description': 'New node created',
                'schema': TypeModel,
            },
            '400': {
                'description': 'The Type is already in the data base',
                'schema': TypeModel,
            },
            '500': {
                'description': 'No JSON data has been received in the body of the request or is bad formated',
                'schema': TypeModel,
            }
        }
    })
    def post(self):
        data = request.get_json()

        tipo = data.get('type')
        if not tipo:
            return {'type': 'This field is required.'}, 400

        def get_type_by_type(tx, tipo):
            return tx.run(
                '''
                MATCH (type:Type)
                WHERE toLower(type.Type) = toLower($type)
                RETURN type
                ''', {'type': tipo}
            ).single()

        db = get_db()
        result = db.read_transaction(get_type_by_type, tipo)
        if result and result.get('type'):
            return {'type': 'Type is already in the data base'}, 400

        def create_type(tx, tipo):
            return tx.run(
                '''
                MATCH (types: Type)
                WITH count(types)+1 as id
                CREATE (type:Type {TypeId: id, Type: $type})
                RETURN type
                ''',
                {
                    'type': tipo
                }
            ).single()

        results = db.write_transaction(create_type, tipo)
        tipo = results['type']
        return serialize_type(tipo), 201
    
class TypesById(Resource):
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Find a type',
        'description': 'Returns a type',
        'responses': {
            '200': {
                'description': 'Whole data of a type',
                'schema': TypeModel,
            }
        }
    })
    def get(self, typeId):
        def get_type_by_id(tx, typeId):
            return tx.run(
                '''
                MERGE (type:Type{TypeId: $type})
                RETURN type
                ''',
                {
                    "type": typeId
                }
            ).single()
        db = get_db()
        result = db.write_transaction(get_type_by_id, typeId)
        return serialize_type(result['type']), 200
    
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Update a type',
        'description': 'update the information of a type',
        'responses': {
            '200': {
                'description': 'Type information updated',
                'schema': TypeModel,
            },
            '400': {
                'description': 'Bad request',
                'schema': TypeModel,
            },
            '500': {
                'description': 'No JSON data has been received in the body of the request or it is bad formated',
                'schema': TypeModel,
            }
        }
    })
    def put(self, typeId):
        data = request.get_json()
        # typeId = data.get('typeId')
        tipo = data.get('type')
        def update_type(tx, typeId, tipo):
            return tx.run(
                '''
                MATCH (t:Type {TypeId: $typeID})
                SET t.Type = $type
                RETURN t
                ''',
                {
                    'typeID': typeId,
                    'type': tipo
                }
            )
        db = get_db()
        result = db.write_transaction(update_type, typeId, tipo)
        return serialize_type(result['t']), 200
    
    @swagger.doc({
        'tags': ['Type'],
        'summary': 'Delete a type',
        'description': 'Delete the information of a type',
        'responses': {
            '200': {
                'description': 'Type information deleted',
                'schema': TypeModel,
            },
            '400': {
                'description': 'Bad request',
                'schema': TypeModel,
            }
        }
    })
    def delete(self, typeId):
        def delete_type(tx, typeId):
            return tx.run(
                '''
                MATCH (t:Type {TypeId: $typeID})
                DELETE t
                ''',
                {
                    'typeID': typeId,
                }
            )
        db = get_db()
        result = db.write_transaction(delete_type, typeId)
        return {'message': 'Node deleted with id '+ typeId}, 200


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
    
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Add Animes',
        'description': 'Add new animes animes',
        'responses': {
            '201': {
                'description': 'A list of animes',
                'schema': TypeModel,
            }
        }
    })
    def post(self):
        data = request.get_json()
        name = data.get('name')
        japanese_name = data.get('japanese_name')
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
        
        def get_anime_by_name(tx, name, japanese_name):
            return tx.run(
                '''
                MATCH (a:Anime)-[]->(t)
                MATCH (s:Studio)-[]->(a)
                WHERE toLower(a.Name) = toLower($name) or toLower(a.Japanese_name) = toLower($japanese_name)
                RETURN a
                ''',
                {
                    'name': name,
                    'japanese_name': japanese_name
                }
            ).single()
        
        db = get_db()
        result = db.write_transaction(get_anime_by_name, name, japanese_name)
        if result:
            return {'error': 'Anime name is already registered'}, 400
        
        def create_anime(tx, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio):
            cypher_query = '''
                match (t:Type {TypeId: $typeId})
                match (s:Studio{StudioId: $studioId})
                match (animes:Anime)
                with count(animes)+1 as id, t as t, s as s
                merge (a:Anime{AnimeID: id, Name: $name, Japanese_name: $japanese_name, Episodes: $episodes, Release_season: $release_season, Tags: $tags, Rating: $rating, Release_year: $release_year, Viewed: False})
                merge (a)-[:TRANSMITTED_IN]->(t)
                merge (s)-[:PRODUCED]->(a)
                return a, t, s
            '''
            return tx.run(cypher_query, {
                'name': name,
                'japanese_name': japanese_name,
                'episodes': episodes,
                'release_season': release_season,
                'tags': tags,
                'rating': rating,
                'release_year': release_year,
                'typeId': tipo,
                'studioId': studio
            }).single()
        
        result = db.write_transaction(create_anime, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio)
        
        return serialize_full_anime(result), 201
        



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

class AnimeListByReleaseYear(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find all Animes whith an especific release year',
        'description': 'Returns all animes with a release year in common',
        'responses': {
            '200': {
                'description': 'A list of animes with the same release year',
                'schema': TypeModel,
            }
        }
    })
    def get(self, release_year):
        def get_animes(tx, release_year):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            # cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(a.Name) contains toLower('" +anime_name + "') or toLower(a.Japanese_name) contains toLower('" +anime_name + "') return a, t, s"
            return list(tx.run(
                '''
                MATCH (a:Anime{Release_year: $release_year})-[]->(t)
                MATCH (s:Studio)-[]->(a)
                RETURN a, s, t
                ''',
                {
                    'release_year': release_year
                }
            ))
        db = get_db()
        result = db.write_transaction(get_animes, release_year)
        return [serialize_full_anime(record) for record in result]

class AnimesById(Resource):
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Find an Anime whith an especific ID',
        'description': 'Returns an animes',
        'responses': {
            '200': {
                'description': 'An animes with the specified ID',
                'schema': TypeModel,
            }
        }
    })
    def get(self, animeId):
        def get_anime_by_id(tx, animeId):
            return tx.run(
                '''
                MATCH (a:Anime {AnimeID: $animeID})-[]->(t)
                MATCH (s:Studio)-[]->(a)
                RETURN a, t, s
                ''',
                {
                    'animeID': animeId
                }
            ).single()
        db = get_db()
        result = db.write_transaction(get_anime_by_id, animeId)
        if not result :
            return {'error', 'Anime not found'}, 404
        return serialize_full_anime(result)
    
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Update an Animes',
        'description': 'Update and return an animes whith an especific ID',
        'responses': {
            '200': {
                'description': 'The new information was saved successfully',
                'schema': TypeModel,
            }
        }
    })
    def put(self, animeId):
        data = request.get_json()
        name = data.get('name')
        japanese_name = data.get('japanese_name')
        episodes = data.get('episodes')
        release_season = data.get('release_season')
        tags = data.get('tags')
        rating = data.get('rating')
        release_year = data.get('release_year')
        viewed = data.get('viewed')

        tipo = data.get('type')
        studio = data.get('studio')
        
        if not name:
            return {'name': 'This field is required.'}, 400
        if not tipo:
            return {'type': 'This field is required.'}, 400
        if not studio:
            return {'studio': 'This field is required.'}, 400
        
        def update_anime(tx, animeId, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio, viewed):
            return tx.run(
                '''
                MATCH (a:Anime{AnimeID: $animeID})-[r:TRANSMITTED_IN]->(ty:Type)
                MATCH (st:Studio)-[p:PRODUCED]->(a)
                MATCH (t:Type{TypeId: $typeId})
                MATCH (s:Studio{StudioId: $studioId})
                SET a.Name= $name, a.Japanese_name = $japanese_name, a.Episodes = $episodes, a.Release_season = $release_season, a.Tags = $tags, a.Rating = $rating, a.Release_year = $release_year, a.Viewed = $viewed
                DELETE r, p
                merge (a)-[:TRANSMITTED_IN]->(ty)
                merge (st)-[:PRODUCED]->(a)
                return a, s, t
                ''',
                {
                    'animeID': animeId,
                    'name': name,
                    'japanese_name': japanese_name,
                    'episodes': episodes,
                    'release_season': release_season,
                    'tags': tags,
                    'rating': rating,
                    'release_year': release_year,
                    'typeId': tipo,
                    'studioId': studio,
                    'viewed': viewed
                }
            ).single()
        db = get_db()
        result = db.write_transaction(update_anime, animeId, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio, viewed)
        return serialize_full_anime(result)
     
     
    @swagger.doc({
        'tags': ['Anime'],
        'summary': 'Delete an Animes',
        'description': 'Delete and return an animes whith an especific ID',
        'responses': {
            '200': {
                'description': 'The information was successfully deleted',
                'schema': TypeModel,
            }
        }
    })
    def delete(self, animeId):
        def delete_anime(tx, animeId):
            return tx.run(
                '''
                MATCH (a:Anime{AnimeID: $animeID})-[p]->()
                MATCH ()-[r]->(a)
                delete r, p, a
                ''',
                {
                    'animeID': animeId
                }
            )
        db = get_db()
        result = db.write_transaction(delete_anime, animeId)
        return {'message': 'The anime was successfully deleted'}, 200

#-------------------------------------
#                                       Demon Slayer: Kimetsu no Yaiba - Entertainment District Arc
#   Creando los endpoints del REST API
#
#-------------------------------------

# Documentation
api.add_resource(ApiDocs,               '/api/v0/docs')

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
