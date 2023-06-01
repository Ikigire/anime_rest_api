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