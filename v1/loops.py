from mongoengine.errors import DoesNotExist

from .models import Squad
from .encoding import dictify

async def join_squad_loop(websocket):
    squad = None

    try:
        while squad is None:
            message = await websocket.receive_json()

            if 'message_type' not in message or 'data' not in message:
                await websocket.send_json({
                    'succeeded': False,
                    'message': 'Invalid message type'
                })

            elif message['message_type'] != 'join':
                await websocket.send_json({
                    'succeeded': False,
                    'message': 'Invalid message type; join a squad first'
                })

            elif 'name' not in message['data'] or 'secret' not in message['data']:
                await websocket.send_json({
                    'succeeded': False,
                    'message': 'Invalid message format'
                })

            else:
                try:
                    squad = Squad.objects.get(
                        name=message['data']['name'],
                        secret=message['data']['secret']
                    )
                    await websocket.send_json({
                        'succeeded': True,
                        'message': 'Squad joined'
                    })
                    return squad

                except DoesNotExist:
                    await websocket.send_json({
                        'succeeded': False,
                        'message': 'Bad squad name or secret'
                    })
    except KeyError:
        pass
