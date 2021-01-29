# wolfpack-server
The backend squad server that enables information sharing for [Wolf Pack].(https://github.com/paulkilla/WarThunderUI)

There's two main parts to work with:

 - Squad Registration (REST)
 - Update Messages (Websockets)

## Squad Registration
Squads are registered by doing a simple `application/json` POST to http://squad.wolfpack.ws/squads :

    {
      "name":  "My Squad Name",
      "secret":  "mysquadsecret"
    }

 - Once registered, any player with the secret can join the squad for a session
 - Squads will  be deleted after 7 days of inactivity


## Update Messages
Update messages work using a websockets based pub/sub model, with two endpoints:

 - ws://squad.wolfpack.ws/pub
 - ws://squad.wolfpack.ws/sub

### Setting up the Websockets
Setting up websockets in JS is pretty easy:

    var pub = new Websocket('ws://squad.wolfpack.ws/pub');
    var sub = new Websocket('ws://squad.wolfpack.ws/sub');

Next, setup a handler function for inbound messages:

    pub.onmessage = function (event) {
      console.log(event.data);
    }
    
    sub.onmessage = function (event) {
      console.log(event.data);
    }

Finally, join a squad  in each socket:

    pub.send(JSON.stringify({
      "message_type": "join",
      "data": {
        "name": "My Squad Name",
        "secret": "mysquadsecret"
      }
    }))
    
    sub.send(JSON.stringify({
      "message_type": "join",
      "data": {
        "name": "My Squad Name",
        "secret": "mysquadsecret"
      }
    }))

### Message Types and Formats
You may have noticed the `message_type` key in the above code samples. There’s three message types to use, that (mostly) follow the same format. Note that the top level attributes (`message_type`, `player`, and `data`) are fixed. Anything in the data dict is unstructured, allowing for publishing of **any** data.

Any data sent to the /pub endpoint will be broadcast to anyone (yourself included) subscribed to the /sub endpoint.

 #### join
Join an existing squad. All squad members can send and receive messages. This is always the first message.

    {    
      "message_type": "join",
      "data": {
        "name": "My Squad Name",
        "secret": "mysquadsecret"
      }
    }

#### squadmate
A message with telemetry from yourself (pub) or another squad mate (sub). 

    {
      "message_type": "squadmate",
      "player": "friendly_player",
      "data": {
        "ias": 302,
        "tas": 334,
        "altitude": 2432
        "etc": "...."
      }
    }

#### enemy
A message with details about an enemy plane (plane type, height etc)

    {    
      "message_type": "enemy", 
      "player": "enemy_player",    
      "data": {    
        "vehicle": "Bf-109",    
        "altitude": 2432    
      }    
    }

## Spinning Up a Local Instance

Required environment variables:

 MONGO_URL
 SQUAD_TTL
 DATA_TTL

I quite like https://direnv.net/ for managing environment variables across multiple dev environments.

    git clone https://github.com/sp4rks/wolfpack-server.git
    cd wolfpack-server
    virtualenv -p python3.7 venv
    source venv/bin/activate
    pip install -r requirements.txt
    python server.py

## Other notes

 - Because the built in telemetry server for War Thunder runs over
   unsecured HTTP, Wolf Pack the wolfpack app and server also use unsecured HTTP to avoid issues with mixed mode AJAX requests
