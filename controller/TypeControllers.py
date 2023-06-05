from flask import request
from flask_restful import Resource
from tools.driver import get_db
from tools.serializer import serialize_type

class TypeList(Resource):
    def get(self):
        def get_types(tx):
            return list(tx.run('MATCH (type:Type) RETURN type'))
        db = get_db()
        result = db.write_transaction(get_types)
        return [serialize_type(record['type']) for record in result]

    def post(self):
        data = request.get_json()

        tipo = data.get('Type')
        if not tipo:
            return {'type': 'This field is required.'}, 400

        def get_type_by_type(tx, tipo):
            return tx.run(
                '''
                MATCH (type:Type)
                WHERE toLower(type.Type) = toLower($type)
                RETURN type ORDER BY type.TypeId
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
                WITH max(types:TypeId)+1 as id
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

    def put(self, typeId):
        data = request.get_json()
        # typeId = data.get('typeId')
        tipo = data.get('Type')
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
