import zmq.asyncio
import logging
import json

class ZMQServer:
    def __init__(self, endpoint):
        context = zmq.asyncio.Context()
        self.poller = zmq.Poller()
        self.server = context.socket(zmq.REP)
        logging.info(f"The endpoint is {endpoint}")
        self.server.bind(endpoint)
    

    async def run(self, dht):
        while True:
            request = await self._recv_json()
            logging.info(f"Received request: {request}")
            await self.handle_request(request, dht)
            

    async def handle_request(self, request, dht):
        operation = request.get("op", None)

        if not operation:
            await self._send_nack()

        if operation == "GET":
            await self._handle_get(request, dht)
        elif operation == "BOOTSTRAP":
            await self._handle_bootstrap(request, dht)
        elif request["op"] == "REGISTER":
            await self._handle_register(request, dht) 
        elif request["op"] == "SET_FOLLOWERS":
            await self._handle_set_followers(request, dht)
        elif request["op"] == "SET_LAST_POST_TIMESTAMP":
            await self._handle_set_last_post_timestamp(request, dht)
        else:
            logging.error(f"Received unknown operation: {operation}")
            await self._send_nack()


    async def _handle_get(self, request, dht):
        body = request.get("body", None)
        if not body:
            await self._send_nack("[GET] body not found")
            return

        key = body.get("key", None)
        if not key:
            await self._send_nack("[GET] key in body not found")
            return

        response = await dht.get(key)
        if not response:
            await self._send_nack("[GET] key not found in dht")
            return

        await self._send_ack(response)


    async def _handle_bootstrap(self, request, dht):
        body = request.get("body", None)
        if not body:
            await self._send_nack()
            return
        
        ip, port = body.get("ip", None), body.get("port", None)
        if not ip or not port:
            await self._send_nack()
            return
        
        await dht.bootstrap_node((ip, port))
        await self._send_ack()


    async def _handle_register(self, request, dht):
        body = request.get("body", None)
        if not body:
            await self._send_nack("[REGISTER] body not found")
            return

        username, ip, port, public_key = body.get("username", None), body.get("ip", None), body.get("port", None), body.get("public_key", None)

        if not username or not ip or not port or not public_key: 
            await self._send_nack("[REGISTER] username | ip | port | public_key not found")
            return 

        user_data = await dht.get(username)
        if user_data:   # Verify if the user already exists
            await self._send_nack("[REGISTER] user already exists")
            return 

        try:
            await dht.set(username, {
                "ip": ip,
                "port": port,
                "followers": [], 
                "public_key": public_key,
                "last_post_timestamp": None
            })
        except Exception:
            await self._send_nack("[REGISTER] dht set new user failed")
            return

        await self._send_ack()

    
    async def _handle_set_followers(self, request, dht):
        body = request.get("body", None)
        if not body:
            await self._send_nack("[SET_FOLLOWERS] cannot get body")
            return

        username, followers = body.get("username", None), body.get("followers", None)
        if not username or followers == None:
            await self._send_nack("[SET_FOLLOWERS] cannot get username or followers")
            return

        content = await dht.get(username)
        if not content:   # Verify if user exists
            await self._send_nack("[SET_FOLLOWERS] dht cannot find username content")
            return

        print("NEW FOLLOWERS IN CONTENT", followers)
        content["followers"] = followers
        try:
            await dht.set(username, content)
        except Exception:
            await self._send_nack("[SET_FOLLOWERS] failed to set username and followers in dht")
            return

        await self._send_ack()
    

    async def _handle_set_last_post_timestamp(self, request, dht):
        body = request.get("body", None)
        if not body:
            await self._send_nack("[SET_LAST_POST_TIMESTAMP] cannot get body")
            return

        username, timestamp = body.get("username", None), body.get("timestamp", None)
        if not username or not timestamp:
            await self._send_nack("[SET_LAST_POST_TIMESTAMP] cannot get username or timestamp")
            return

        content = await dht.get(username)
        if not content:   # Verify if user exists
            await self._send_nack("[SET_LAST_POST_TIMESTAMP] dht cannot find username content")
            return

        content["last_post_timestamp"] = timestamp
        try:
            await dht.set(username, content)
        except Exception:
            await self._send_nack("[SET_FOLLOWERS] failed to set username and followers in dht")
            return

        await self._send_ack()


    async def _send_ack(self, body=None):
        if body:
            await self._send_json({"status": "ACK", "body": body})
        else:
            await self._send_json({"status": "ACK"})


    async def _send_nack(self, error="unknown"):
        await self._send_json({"status": "NACK", "error": error})


    async def _recv_json(self):
        return json.loads(await self.server.recv())
    

    async def _send_json(self, dict):
        await self.server.send(json.dumps(dict).encode("utf-8"))
