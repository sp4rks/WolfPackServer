from datetime import datetime
import os

import mongoengine as me

MONGO_URL = os.environ['MONGO_URL']
SQUAD_TTL = 7 * 86400
DATA_TTL = 60

me.connect(host=MONGO_URL)

class Squad(me.Document):
    name = me.StringField(required=True, unique=True)
    secret = me.StringField(required=True)
    last_update = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {
                'fields': ['last_update'],
                'expireAfterSeconds': SQUAD_TTL
            }
        ]
    }

    def clean(self):
        self.last_update = datetime.utcnow()

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)


class Enemy(me.Document):
    squad = me.ReferenceField(Squad, required=True)
    player = me.StringField(required=True, unique=True)
    data = me.DictField(default={})
    message_type = me.StringField(default='enemy')
    last_update = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {
                'fields': ['squad', 'player'],
                'unique': True
            },
            {
                'fields': ['last_update'],
                'expireAfterSeconds': DATA_TTL
            }
        ]
    }

    def clean(self):
        self.message_type = "enemy"
        self.last_update = datetime.utcnow()

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)


class SquadMate(me.Document):
    squad = me.ReferenceField(Squad, required=True)
    player = me.StringField(required=True, unique=True)
    data = me.DictField(default={})
    message_type = me.StringField(default='enemy')
    last_update = me.DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            {
                'fields': ['squad', 'player'],
                'unique': True
            },
            {
                'fields': ['last_update'],
                'expireAfterSeconds': DATA_TTL
            }
        ]
    }

    def clean(self):
        self.message_type = "squadmate"
        self.last_update = datetime.utcnow()

    def __str__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)
