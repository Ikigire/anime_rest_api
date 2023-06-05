from flask import request
from flask_restful import Resource
from tools.driver import get_db
from tools.serializer import serialize_full_anime, serialize_anime

class AnimeList(Resource):
    def get(self):
        def get_animes(tx):
            return list(tx.run('MATCH (anime:Anime) RETURN anime'))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_anime(record['anime']) for record in result]

class FullAnimeList(Resource):
    def get(self):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a, t, s"))
        db = get_db()
        abc = 0
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]

    def post(self):
        data = request.get_json()
        print(data)
        name = data.get('Name')
        print('\n\nData name:' + name)
        japanese_name = data.get('Japanese_name')
        print('\n\nData japanese_name:' + japanese_name)
        release_season = data.get('Release_season')
        print('\n\nData release_season:' + release_season)
        tags = data.get('Tags')
        print('\n\nData tags:' + tags)
        rating = float(data.get('Rating'))
        print('\n\nData rating:' + str(rating))
        release_year = int(data.get('Release_year'))
        print('\n\nData release_year:' + str(release_year))
        episodes = int(data.get('Episodes'))
        print('\n\nData episodes:' + str(episodes))

        tipo = int(data.get('TypeId'))
        print('\n\nData tipo:' + str(tipo))
        studio = int(data.get('StudioId'))
        print('\n\nData studio:' + str(studio))
        
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
        
        def create_anime(tx, name, japanese_name, episodes, release_season, tags, rating, release_year, typeId, studioId):
            return tx.run(
                '''
                match (tipo:Type {TypeId: $type})
                match (studio:Studio{StudioId: $studio})
                match (animes:Anime)
                with max(animes:AnimeID)+1 as id, tipo as t, studio as s
                create (a:Anime{AnimeID: id, Name: $anime_name, Japanese_name: $anime_j_name, Episodes: $anime_episodes, Release_season: $anime_season, Tags: $anime_tags, Rating: $anime_rating, Release_year: $anime_year, Viewed: False})
                merge (a)-[:TRANSMITTED_IN]->(t)
                merge (s)-[:PRODUCED]->(a)
                return a, t, s
                ''',
                {
                    "type": typeId,
                    "studio": studioId,
                    "anime_name": name,
                    "anime_j_name": japanese_name,
                    "anime_episodes": episodes,
                    "anime_season": release_season,
                    "anime_tags": tags,
                    "anime_rating": rating,
                    "anime_year": release_year
                }
            ).single()
        # def create_anime(tx, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio):
        #     cypher_query = '''
        #         match (type:Type {TypeId: $typeId})
        #         match (studio:Studio{StudioId: $studioId})
        #         match (animes:Anime)
        #         with count(animes)+1 as id, type as t, studio as s
        #         merge (a:Anime{AnimeID: id, Name: $name, Japanese_name: $japanese_name, Episodes: $episodes, Release_season: $release_season, Tags: $tags, Rating: $rating, Release_year: $release_year, Viewed: False})
        #         merge (a)-[:TRANSMITTED_IN]->(t)
        #         merge (s)-[:PRODUCED]->(a)
        #         return a, t, s
        #     '''
        #     return tx.run(cypher_query, {
        #         'name': name,
        #         'japanese_name': japanese_name,
        #         'episodes': episodes,
        #         'release_season': release_season,
        #         'tags': tags,
        #         'rating': rating,
        #         'release_year': release_year,
        #         'typeId': tipo,
        #         'studioId': studio
        #     }).single()
        
        result = db.write_transaction(create_anime, name, japanese_name, episodes, release_season, tags, rating, release_year, tipo, studio)
        print(result)
        if not result or result == None:
            return {'error', 'Anime not saved due an internal server error'}, 409
        return serialize_full_anime(result), 201
        



class AnimeListByStudio(Resource):
    def get(self, studio_name):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(s.Name) contains toLower('" + studio_name + "') return a, t, s ORDER BY a.Release_year DESC"
            return list(tx.run(cypher_query))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]

class AnimeListByName(Resource):
    def get(self, anime_name):
        def get_animes(tx):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(a.Name) contains toLower('" +anime_name + "') or toLower(a.Japanese_name) contains toLower('" +anime_name + "') return a, t, s ORDER BY a.Release_year DESC"
            return list(tx.run(cypher_query))
        db = get_db()
        result = db.write_transaction(get_animes)
        return [serialize_full_anime(record) for record in result]

class AnimeListByReleaseYear(Resource):
    def get(self, release_year):
        def get_animes(tx, release_year):
            # return list(tx.run("match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) return a.AnimeID as AnimeID, a.Name as Name, a.Japanese_name as Japanese_name, a.Episodes as Episodes, a.Release_season as Release_season, a.Tags as Tags, a.Rating as Rating, a.Release_year as Release_year, a.Viewed as Viewed, t.Type as Type, s.Name as Studio"))
            # cypher_query = "match (a:Anime)-[]->(t) match (s:Studio)-[]->(a) where toLower(a.Name) contains toLower('" +anime_name + "') or toLower(a.Japanese_name) contains toLower('" +anime_name + "') return a, t, s"
            return list(tx.run(
                '''
                MATCH (a:Anime{Release_year: $release_year})-[]->(t)
                MATCH (s:Studio)-[]->(a)
                RETURN a, s, t ORDER BY a.Release_year DESC
                ''',
                {
                    'release_year': release_year
                }
            ))
        db = get_db()
        result = db.write_transaction(get_animes, release_year)
        return [serialize_full_anime(record) for record in result]

class AnimesById(Resource):
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
    
    def put(self, animeId):
        data = request.get_json()
        name = data.get('Name')
        japanese_name = data.get('Japanese_name')
        release_season = data.get('Release_season')
        tags = data.get('Tags')
        rating = float(data.get('Rating'))
        release_year = int(data.get('Release_year'))
        episodes = int(data.get('Episodes'))
        viewed = bool(data.get('Viewed'))
        try:
            tipo = int(data.get('TypeId'))
            studio = int(data.get('StudioId'))
        except :
            tipo = None
            studio = None
        
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
                merge (a)-[:TRANSMITTED_IN]->(t)
                merge (s)-[:PRODUCED]->(a)
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
        db.write_transaction(delete_anime, animeId)
        return {'message': 'The anime was successfully deleted'}, 200
