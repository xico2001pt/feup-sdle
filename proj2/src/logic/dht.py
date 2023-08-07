import json

from kademlia.network import Server
import asyncio
import sys
import logging
import os


class Kademlia():
    def __init__(self, port):
        self.port = int(port)

    async def start(self):
        self.server = Server()
        await self.server.listen(self.port)

    # node is a tuple e.g. ("123.123.123.123", 5678)
    async def bootstrap_node(self, node):
        await self.server.bootstrap([node])

    async def set(self, key, value):
        await self.server.set(key, json.dumps(value))

    async def get(self, key):
        try:
            content = await self.server.get(key)
            return json.loads(content)
        except Exception:
            return None

    def stop(self):
        self.server.stop()


async def run():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    dht = Kademlia(int(sys.argv[1]))
    await dht.start()

    bootstrap_port = int(os.getenv("BLUESEA_PORT"))
    logging.info(bootstrap_port)

    await dht.bootstrap_node(("127.0.0.1", bootstrap_port))
    await dht.set("test", "test")
    dht.stop()


if __name__ == "__main__":
    asyncio.run(run())
