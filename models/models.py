from flask_restful_swagger_2 import Schema

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
