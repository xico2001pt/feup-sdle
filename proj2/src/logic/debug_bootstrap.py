import asyncio

from kademlia.network import Server

server = Server()

def create_bootstrap_node():
    loop = asyncio.new_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(8468))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()

def main():
    create_bootstrap_node()

if __name__ == "__main__":
    main()