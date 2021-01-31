import os
import asyncio
from urllib.parse import urlparse

from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
from starlette.routing import Route, WebSocketRoute
from mongoengine.errors import NotUniqueError, FieldDoesNotExist, DoesNotExist

from .models import Squad
from .loops import join_squad_loop
from .handlers import handle_enemy, handle_squadmate, handle_outbound
from .encoding import dictify


MONGO_URL = os.environ['MONGO_URL']
MONGO_DB = urlparse(MONGO_URL).path.replace('/', '')

async def create_squad(request):
    body = await request.json()

    if 'name' not in body or 'secret' not in body:
        return JSONResponse(status_code=400)

    try:
        squad = Squad(**body)
        squad.save()
        return JSONResponse(dictify(squad), status_code=201)

    except NotUniqueError:
        try:
            Squad.objects.get(name=body['name'], secret=body['secret'])
            return JSONResponse(status_code=200)
        except DoesNotExist:
            return JSONResponse(status_code=409)

    except FieldDoesNotExist:
        return JSONResponse(status_code=400)

    except Exception as e:
        print(f'1: {e}')
        squad.delete()
        return JSONResponse(status_code=500)


async def publish(websocket):
    await websocket.accept()

    squad = await join_squad_loop(websocket)
    while True:
        message = await websocket.receive_json()

        if 'message_type' in message and 'data' in message:

            if message['message_type'] == 'enemy':
                result = await handle_enemy(squad, message)
                await websocket.send_json(result)

            elif message['message_type'] == 'squadmate':
                result = await handle_squadmate(squad, message)
                await websocket.send_json(result)

            elif message['message_type'] == 'join':
                await websocket.send_json({
                    'success': False,
                    'message': 'Squad already joined'
                })

            else:
                await websocket.send_json({
                    'success': False,
                    'message': 'Unrecognised message type'
                })

        else:
            await websocket.send_json({
                'success': False,
                'message': 'Invalid message format'
            })

    await websocket.close()

async def subscribe(websocket):

    await websocket.accept()

    client = AsyncIOMotorClient(MONGO_URL, io_loop=asyncio.get_event_loop())
    db = client.get_database(MONGO_DB)

    squad = await join_squad_loop(websocket)

    connected = True
    resume_token = None
    pipeline = [{
        '$match':{
            '$and': [
                { 'operationType': { '$in': ['insert', 'update'] } }
            ]
        }
    }]

    while connected:
        try:
            async with db.watch(pipeline) as stream:
                async for change in stream:
                    outbound_message = await handle_outbound(squad, change)
                    if outbound_message:
                        await websocket.send_json(outbound_message)

        except PyMongoError as e:
            if resume_token is None:
                print(f'2: {e}')
                connected = False
            else:
                async with db.collection.watch(pipeline, resume_after=resume_token) as stream:
                    async for change in stream:
                        outbound_message = await handle_outbound(squad, change)
                        if outbound_message:
                            await websocket.send_json(outbound_message)

        except KeyboardInterrupt:
            print('Keyboard Interrupt: terminating subscribe loop')
            connected = False
        except WebSocketDisconnect:
            print('Websocket Disconnect: terminating subscribe loop')
            connected = False

    await websocket.close()


routes = [
    Route('/squads', create_squad, methods=['POST']),
    WebSocketRoute('/pub', publish),
    WebSocketRoute('/sub', subscribe)
]
