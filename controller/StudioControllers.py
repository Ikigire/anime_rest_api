from flask import request
from flask_restful import Resource
from tools.driver import get_db

from tools.serializer import serialize_studio

class StudioList(Resource):
    
    def get(self):
        def get_studios(tx):
            return list(tx.run('MATCH (studio:Studio) RETURN studio ORDER BY toLower(lTrim(studio.Name))'))
        db = get_db()
        result = db.write_transaction(get_studios)
        return [serialize_studio(record['studio']) for record in result]
    
    def post(self):
        data = request.get_json()

        name = data.get('Name')
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
                WITH max(studios:StudioId)+1 as id
                CREATE (studio:Studio {StudioId: id, Name: $name})
                RETURN studio
                ''',
                {
                    'name': name
                }
            ).single()

        results = db.write_transaction(create_studio, name)
        studio = results['studio']
        return serialize_studio(studio), 201

class StudioById(Resource):
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

    def put(self, studioId):
        data = request.get_json()
        # typeId = data.get('typeId')
        name = data.get('Name')
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
