import json
from datetime import datetime

from mongoengine import Document
from bson.objectid import ObjectId


class DocumentEncoder(json.JSONEncoder):
    def default(self, obj): # pylint: disable=arguments-differ
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Document):
            return obj.to_mongo().to_dict()

        return json.JSONEncoder.default(self, obj)


encoder = DocumentEncoder()

def stringify(document):
    return encoder.encode(document)

def dictify(document):
    return json.loads(encoder.encode(document))
