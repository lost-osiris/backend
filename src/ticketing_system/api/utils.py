import os
import pymongo
import re
from bson import ObjectId
from urllib.parse import quote_plus
from pymongo.cursor import Cursor


def to_title_case(string):
    string = string.replace("-", " ")
    string = re.sub(r"\w\S*", lambda txt: txt.group(0).capitalize(), string)
    return string


def alphanumeric_check(data):
    if data.replace(" ", "").isalnum():
        data.replace(" ", "-")
    else:
        return False


def _json_ready(data):
    if isinstance(data, ObjectId):
        return str(data)
    # elif instance(data, datetime.datetime):
    #     return str(data)
    else:
        return data


def prepare_json(data):
    if isinstance(data, Cursor):
        return prepare_json(list(data))

    if isinstance(data, dict):
        output = {}
        for k, v in data.items():
            key = k
            if k == "_id":
                key = "id"

            if isinstance(v, dict) or isinstance(v, list) or isinstance(v, set):
                output[key] = prepare_json(v)
            else:
                output[key] = _json_ready(v)

        return output

    elif isinstance(data, list) or isinstance(data, set):
        output = []
        for value in data:
            if (
                isinstance(value, dict)
                or isinstance(value, list)
                or isinstance(value, set)
            ):
                output.append(prepare_json(value))
            else:
                output.append(_json_ready(value))

        return output
    else:
        return _json_ready(data)


def get_db_client(db="test"):
    USERNAME = quote_plus(os.getenv("DB_USERNAME"))
    PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
    URI = f"mongodb+srv://{USERNAME}:{PASSWORD}@cluster0.81uebtg.mongodb.net/?retryWrites=true&w=majority"

    return pymongo.MongoClient(URI)[db]
