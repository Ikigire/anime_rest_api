import ast
import os
from dotenv import find_dotenv, load_dotenv
from flask import g
from neo4j import GraphDatabase


load_dotenv(find_dotenv())

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

driver = GraphDatabase.driver(DATABASE_URL, auth=(DATABASE_USERNAME, str(DATABASE_PASSWORD)))

def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db