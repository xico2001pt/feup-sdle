import logging
import sys
import zmq
import sys
import socket
import os
import pathlib
import random 
from communication.request import *
from communication.reply import *
from io_utils.client_io import * 

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

REQUEST_TIMEOUT = 5000  # miliseconds
REQUEST_RETRIES = 3
SERVER_ENDPOINT = "tcp://localhost:9001"

class Client:
    def __init__(self, client_dir):
        self.client_dir = client_dir
        self.__connect()

        try:
            self.__get_id()
            self.operation_counter = ClientIO.read_client_counter(self.client_dir)
            self.last_publications_read = ClientIO.read_client_topics(self.client_dir)
        except ConnectionError as e:
            raise e
        except IOError as e: 
            raise e
        except ValueError as e:
            raise e

    def __connect(self):
        self.context = zmq.Context()
        self.client = self.context.socket(zmq.REQ)
        logging.info("Connecting to server...")
        self.client.connect(SERVER_ENDPOINT)
    
    def __get_id(self):
        try:
            self.client_id = ClientIO.read_client_id(self.client_dir)
        except IOError as e:
            raise e
        
        if not self.client_id:
            response = send_message(self.context, self.client, create_id_request())
            
            if not response:
                raise ConnectionError("Unable to setup initial server handshake")
            
            self.client, reply = response
            self.client_id = reply.body['id']
            try:
                ClientIO.save_client_id(self.client_dir, self.client_id) 
            except IOError as e:
                raise e

        logging.info(f"Client id = {self.client_id}")

    def __del__(self):
        logging.info("Disconnecting from server...")
        if self.context: 
            self.context.destroy()

    def get(self, topic_id):
        if not topic_id in self.last_publications_read:
            return False, "Client is not subscribed to topic " + topic_id
        
        request = create_get_request(topic_id, self.client_id, self.last_publications_read[topic_id])
        response = send_message(self.context, self.client, request)
        
        if response:
            self.client, reply = response
            if reply.reply_type == ReplyType.ACK:
                publication_id = reply.body['publication_id']
                if publication_id == -1:
                    return False, f"All publications from {topic_id} were already read"

                publication = reply.body['publication']
                self.last_publications_read[topic_id] = publication_id
                
                try: 
                    ClientIO.save_client_topics(self.client_dir, self.last_publications_read)
                except IOError as e: 
                    return False, str(e)

                return True, publication
            elif reply.reply_type == ReplyType.NAK:
                return False, reply.body["error_message"]
    
        return False, "Server is offline"

    def __randomize_client_counter(self):
        while True:
            new_counter = random.randint(1, 10000000)
            if self.operation_counter != new_counter:
                self.operation_counter = new_counter
                break

    def put(self, topic_id, publication):
        self.__randomize_client_counter()
        try: 
            ClientIO.save_client_counter(self.client_dir, self.operation_counter)
        except IOError as e: 
            return False, str(e)

        request = create_put_request(topic_id, self.client_id, self.operation_counter, publication)
        response = send_message(self.context, self.client, request)

        if response:
            self.client, reply = response
            if(reply.reply_type == ReplyType.ACK):
                return True, ""
            elif reply.reply_type == ReplyType.NAK:
                return False, reply.body["error_message"]
        
        return False, f"Server is offline"

    def subscribe(self, topic_id):
        if topic_id in self.last_publications_read: 
            return False, f"Client is already subscribed to topic {topic_id}"

        request = create_subscribe_request(topic_id, self.client_id)
        response = send_message(self.context, self.client, request)

        if response:
            self.client, reply = response

            if reply.reply_type == ReplyType.ACK:
                try: 
                    self.last_publications_read[topic_id] = int(reply.body['last_publication_id'])
                    ClientIO.save_client_topics(self.client_dir, self.last_publications_read)
                except IOError as e: 
                    return False, str(e)
                except ValueError: 
                    return False, "Unable to parse last_publication_id from response to integer"
                return True, ""
            elif reply.reply_type == ReplyType.NAK:
                return False, reply.body["error_message"]
        
        return False, "Server is offline"
    
    def unsubscribe(self, topic_id):
        if topic_id not in self.last_publications_read: 
            return False, f"Client is not subscribed to topic {topic_id}"

        request = create_unsubscribe_request(topic_id, self.client_id)
        response = send_message(self.context, self.client, request)

        if response:
            self.client, reply = response
            if(reply.reply_type == ReplyType.ACK):
                self.last_publications_read.pop(topic_id, None)
                try:
                    ClientIO.save_client_topics(self.client_dir, self.last_publications_read)
                except IOError as e:
                    return False, str(e)
                return True, ""
            elif reply.reply_type == ReplyType.NAK:
                return False, reply.body["error_message"]

        return False, "Server is offline"

def send_message(context, client, message):
    request = str(message).encode()
    logging.info("Sending (%s)", request)

    if client == None or client.closed:
        client = context.socket(zmq.REQ)
        client.connect(SERVER_ENDPOINT)

    client.send(request)
    
    retries_left = REQUEST_RETRIES
    while True:
        if (client.poll(REQUEST_TIMEOUT) & zmq.POLLIN) != 0:
            reply = Reply.from_json(client.recv())
            logging.info("Server replied (%s)", reply)
            break

        retries_left -= 1

        logging.warning("No response from server")  # Socket is confused, close it
        client.setsockopt(zmq.LINGER, 0)
        client.close()

        if retries_left == 0:
            logging.error("Server seems to be offline, abandoning")
            return None

        logging.info("Reconnecting to server...")   # Create new connection
        client = context.socket(zmq.REQ)
        client.connect(SERVER_ENDPOINT)
        logging.info("Resending (%s)", request)
        client.send(request)
    
    return client, reply