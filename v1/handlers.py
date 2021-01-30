from datetime import datetime

from mongoengine.errors import DoesNotExist

from .models import Enemy, SquadMate
from .encoding import dictify


async def upsert(model, squad, message):

    model = globals()[model]

    try:
        player = model.objects.get(
            squad=squad,
            player=message['player']
        )
        return player.update(data=message['data'], last_update=datetime.utcnow())

    except DoesNotExist:
        player = model(
            squad=squad,
            player=message['player'],
            data=message['data'],
            last_update=datetime.utcnow()
        )
        return player.save()


async def handle_enemy(squad, message):
    result = await upsert('Enemy', squad, message)

    if result:
        return {'success': True}
    else:
        return {'success': False, message: 'An unknown error occurred'}

async def handle_squadmate(squad, message):
    result = await upsert('SquadMate', squad, message)

    if result:
        return {'success': True}
    else:
        return {'success': False, message: 'An unknown error occurred'}

async def handle_outbound(squad, change):
    try:
        collection = change['ns']['coll']
        doc_id = change['documentKey']['_id']

        if collection == 'enemy':
            enemy = Enemy.objects.get(id=doc_id)
            if enemy.squad == squad:
                return dictify(enemy)
            else:
                return None

        elif collection == 'squadmate':
            doc_id = change['documentKey']['_id']
            squadmate = SquadMate.objects.get(id=doc_id)
            if squadmate.squad == squad:
                return dictify(squadmate)
            else:
                return None

        else:
            print('Attempted to dispatch unrecognised message type')

    except KeyError:
        print('Attempted to dispatch unrecognised message format')

    return None
