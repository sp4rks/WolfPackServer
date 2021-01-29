from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount

from v1.app import routes as v1_routes


async def base(request):
    return JSONResponse({
        'name': 'Wolfpack Squad Server'
    })

routes = [
    Route('/', endpoint=base),
    Mount('/v1', routes=v1_routes)
]

app = Starlette(routes=routes)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'server:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
