import os

from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
from mongoengine.errors import NotUniqueError, FieldDoesNotExist

from models import Squad
from loops import join_squad_loop
from handlers import handle_enemy, handle_squadmate, handle_outbound
from encoding import dictify

app = Starlette()

MONGO_URL = os.environ['MONGO_URL']

client = AsyncIOMotorClient(MONGO_URL)
db = client.wptest

@app.route('/', methods=['GET'])
async def homepage(request):
    return JSONResponse({
        'name': 'Wolfpack Squad Server'
    })

@app.route('/squads', methods=['POST'])
async def create_squad(request):
    body = await request.json()

    if 'name' not in body or 'secret' not in body:
        return JSONResponse(status_code=400)

    try:
        squad = Squad(**body)
        squad.save()
        return JSONResponse(dictify(squad), status_code=201)

    except FieldDoesNotExist:
        return JSONResponse(status_code=400)

    except NotUniqueError:
        return JSONResponse(status_code=409)

    except Exception as e:
        print(f'1: {e}')
        squad.delete()
        return JSONResponse(status_code=500)


@app.websocket_route('/pub')
async def publish(websocket):
    await websocket.accept()

    squad = await join_squad_loop(websocket)

    while True:
        message = await websocket.receive_json()

        if 'type' in message and 'data' in message:

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

@app.websocket_route('/sub')
async def subscribe(websocket):
    await websocket.accept()

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


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'server:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
