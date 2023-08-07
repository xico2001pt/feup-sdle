import asyncio
import os
import logging
from pathlib import Path
import sys

from dht import Kademlia
from server import ZMQServer

IPC_PATH_DIR = "/tmp/kademlia/"

async def run():
    port = os.getenv("BLUESEA_PORT")
    logging.info(port)

    dht = Kademlia(port)
    await dht.start()

    bootstrap_node = os.getenv("BLUESEA_BOOTSTRAP_NODE")
    if bootstrap_node:
        bootstrap_node = bootstrap_node.split(":")
        boostrap_ip, bootstrap_port = bootstrap_node[0], int(bootstrap_node[1])
        await dht.bootstrap_node((boostrap_ip, bootstrap_port))

    Path(IPC_PATH_DIR).mkdir(parents=True, exist_ok=True)
    Path(IPC_PATH_DIR + port).touch(exist_ok=True)

    server = ZMQServer(f"ipc://{IPC_PATH_DIR}{port}")
    await server.run(dht)

if __name__ == '__main__':
    asyncio.run(run())
