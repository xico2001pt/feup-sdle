import logging
import zmq
import uuid
import sched
import time
from communication.reply import *
from communication.request import *
from io_utils.server_io import *

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

ENDPOINT = "tcp://*:9001"
GARBAGE_COLLECT_DELAY = 5*60    # seconds

class Server:
    def __init__(self):
        self.context, self.server = self.bind()

        # File handling
        ServerIO.create_server_dir()

        self.publications = ServerIO.read_all_publications()
        if self.publications == None:
            raise IOError

        self.subscribers = ServerIO.read_all_subscribers()
        if self.subscribers == None:
            raise IOError

        self.client_counters = ServerIO.read_client_counters()
        if self.client_counters == None:
            raise IOError
        
        # Setup scheduler
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.scheduler.enter(GARBAGE_COLLECT_DELAY, 0, self.garbage_collect)
        self.scheduler.enter(0, 1, self.handle_request)

    def bind(self):
        context = zmq.Context()
        server = context.socket(zmq.REP)
        server.bind(ENDPOINT)
        return context, server

    def run(self): 
        while True:
            self.scheduler.run()
    
    def handle_request(self):
        request = self.server.recv()    # This action is blocking, garbage collection is only executed after a request has been received
        request = Request.from_json(request.decode())
        logging.info(f"Received request: {request}")
        reply = self.process_request(request)
        self.server.send(str(reply).encode())
        self.scheduler.enter(0, 1, self.handle_request)
        
            
    def process_request(self, request):
        if request.request_type == RequestType.GET:
            return self.process_get(request) 
        elif request.request_type == RequestType.PUT:
            return self.process_put(request)
        elif request.request_type == RequestType.SUB:
            return self.process_sub(request)
        elif request.request_type == RequestType.UNSUB:
            return self.process_unsub(request)
        elif request.request_type == RequestType.REQUEST_ID:
            return self.process_id_request(request)
        return create_nak("Invalid operation type")

    def process_get(self, request):
        if request.topic not in self.publications:
            logging.info(f"Topic not found: {request.topic}")
            return create_nak("Topic not found")

        for publication_id, publication in self.publications[request.topic].items():
            try: 
                last_publication_id = int(request.body['last_publication_id'])
            except ValueError:
                logging.error("Unable to parse last_publication_id from request to integer")
                return create_nak("Invalid message format")

            if publication_id > last_publication_id:
                if not ServerIO.update_subscriber(request.topic, request.client_id, last_publication_id):
                    return create_nak("Unable to update server status")
                self.subscribers[request.topic][request.client_id] = last_publication_id
                return create_get_ack(publication, publication_id)

        logging.info(f"All messages already read.")
        return create_empty_get_ack()
        
    def process_put(self, request):    
        # verify if the topic exists 
        if not request.topic in self.publications:
            print(self.publications)
            logging.log(logging.ERROR, f"Topic {request.topic} does not exist")
            return create_nak("Topic not found")

        # verify if client_counter is not repeated
        if request.client_id in self.client_counters and self.client_counters[request.client_id] == request.body["counter"]:
            logging.log(logging.ERROR, f"Client {request.client_id} already sent a message with counter {request.body['counter']}")
            return create_nak("Duplicated message")

        # obtain highest message id for publication
        last_publication_id = 0
        if request.topic in self.publications and len(self.publications[request.topic].keys()) > 0:
            last_publication_id = list(self.publications[request.topic].keys())[-1]
        current_publication_id = last_publication_id + 1
            
        # write publication and client counter to file
        if not ServerIO.save_publication(request.topic, current_publication_id, request.body['publication']):
            logging.log(logging.ERROR, f"Could not save publication {request.body['publication']} to topic {request.topic}")
            return create_nak("Unable to update server status")
        
        if not ServerIO.save_client_counter(request.client_id, request.body['counter']):
            logging.log(logging.ERROR, f"Could not save client counter {request.body['counter']} for client {request.client_id}")
            return create_nak("Unable to update server status") 

        # save publication and client counter to memory
        self.publications[request.topic][current_publication_id] = request.body['publication']

        self.client_counters[request.client_id] = request.body['counter']
        
        return create_put_ack(current_publication_id)
    
    def process_sub(self, request):
        ServerIO.create_topic_dir(request.topic)    # Create topic if it does not exist
        if not request.topic in self.publications:
            self.publications[request.topic] = {}   # Create topic in memory if it does not exist

        last_publication_id = 0
        if request.topic in self.publications and len(self.publications[request.topic].keys()) > 0:
            logging.error(f"{self.publications[request.topic]}, {self.publications[request.topic].keys()}")
            last_publication_id = max(self.publications[request.topic], key=int)

        if not ServerIO.add_subscriber(request.topic, request.client_id, last_publication_id):
            return create_nak("Unable to update server status")
        
        if request.topic in self.subscribers:
            self.subscribers[request.topic][request.client_id] = last_publication_id
        else:
            self.subscribers[request.topic] = {request.client_id: last_publication_id}

        return create_sub_ack(last_publication_id)
        
    
    def process_unsub(self, request):
        if not request.topic in self.subscribers:
            logging.log(logging.ERROR, f"Topic {request.topic} does not exist")
            return create_nak("Topic not found")

        if not request.client_id in self.subscribers[request.topic]:
            logging.log(logging.ERROR, f"Client {request.client_id} is not subscribed to topic {request.topic}")
            return create_nak("Client is not subscribed to topic")

        if not ServerIO.remove_subscriber(request.topic, request.client_id):
            logging.log(logging.ERROR, f"Could not save client unsubscribe from {request.topic} for client {request.client_id}")
            return create_nak("Unable to update server status") 
            
        self.subscribers[request.topic].pop(request.client_id)

        if len(self.subscribers[request.topic]) == 0:
            ServerIO.delete_topic_dir(request.topic)
            self.subscribers.pop(request.topic)
            self.publications.pop(request.topic, None)
    
        return create_unsub_ack()

    def process_id_request(self, request):
        new_id = ""
        while True:
            new_id = uuid.uuid4().hex
            if new_id not in self.client_counters:
                break
        self.client_counters[new_id] = -1   # new id registered
        return create_id_ack(new_id)

    def garbage_collect(self):
        logging.info("Starting garbage collection process")
        self.scheduler.enter(GARBAGE_COLLECT_DELAY, 1, self.garbage_collect)

        if ServerIO.clean_client_counters() == None: 
            logging.error("Unable to clean client_counters")
            return None

        for topic_id in self.subscribers: 
            if ServerIO.clean_subscribers(topic_id) == None:
                logging.error("Unable to clean the subscribers for " + topic_id)
                return None

        for topic_id in self.publications:
            last_publication_received = min(self.subscribers[topic_id].values())
            if ServerIO.clean_publications(topic_id, last_publication_received) == None: 
                logging.error("Unable to clean received publications for " + topic_id)
                return None

def main():
    try:
        server = Server()
    except IOError:
        exit(1)
    server.run()

if __name__ == "__main__":
    main()
