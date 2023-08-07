from .file_io import FileIO
import pathlib
import shutil
from collections import OrderedDict
import os

SERVER_DIR = "./src/server_data"
TOPICS_DIR = SERVER_DIR + "/topics"

class ServerIO:

    def create_server_dir():
        pathlib.Path(TOPICS_DIR).mkdir(parents=True, exist_ok=True)
        pathlib.Path(f"{SERVER_DIR}/client_counters.csv").touch(exist_ok=True)

    # ============================= TOPICS =============================

    def create_topic_dir(topic_id):
        topic_path = f"{TOPICS_DIR}/{topic_id}"
        pathlib.Path(topic_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(f"{topic_path}/publications.csv").touch(exist_ok=True)
        pathlib.Path(f"{topic_path}/subscribers.csv").touch(exist_ok=True)

    def delete_topic_dir(topic_id):
        shutil.rmtree(pathlib.Path(f"{TOPICS_DIR}/{topic_id}"))

    # ============================= PUBLICATIONS =============================

    def read_publications(topic_id):
        result, lines = FileIO.read_lines(f"{TOPICS_DIR}/{topic_id}/publications.csv")
        if not result:
            print(f"Error when reading topic '{topic_id}': {lines}")
            return None
        
        topic_publications = OrderedDict()
        for line in lines:
            topic_line = line.split(',')
            pub_id, publication = topic_line[0], ",".join(topic_line[1:])
            try:
                topic_publications[int(pub_id)] = publication
            except ValueError:
                print(f"Invalid message ID format (not int)")
                return None
        return topic_publications

    def read_all_publications():
        if not pathlib.Path(TOPICS_DIR).exists():
            return {}

        publications = {}
        for topic in os.listdir(TOPICS_DIR):
            topic_publications = ServerIO.read_publications(topic)
            if topic_publications == None:
                return None
            publications[topic] = topic_publications
        return publications

    def save_publication(topic_id, pub_id, publication):
        result, error_str = FileIO.append_line(f"{TOPICS_DIR}/{topic_id}/publications.csv", f"{pub_id},{publication}")
        if not result:
            print(f"Error when appending publication '{pub_id}' to topic '{topic_id}': {error_str}")
        return result

    # Garbage collection
    def clean_publications(topic_id, last_publication_received):
        publications = ServerIO.read_publications(topic_id)
        if publications == None:
            return None
        
        result, error_str = FileIO.write_lines(f"{TOPICS_DIR}/{topic_id}/publications.csv", [f"{pub_id},{publication}" for pub_id, publication in publications.items() if pub_id > last_publication_received])
        if not result:
            print(f"Error when writing publications of topic '{topic_id}': {error_str}")
            return None
        return publications

    # ============================= SUBSCRIBERS =============================
    
    def read_subscribers(topic_id):
        result, lines = FileIO.read_lines(f"{TOPICS_DIR}/{topic_id}/subscribers.csv")
        if not result:
            print(f"Error when reading subscribers from topic '{topic_id}': {lines}")
            return None

        subscribers = {}
        for line in lines:
            subscriber_line = line.split(",")
            try:
                operation, client_id = subscriber_line[0], subscriber_line[1]
                if operation == 'SUB':
                    if client_id in subscribers:
                        print(f"Warning when reading subscribers from topic '{topic_id}': consecutive SUB operations without UNSUB in between")
                    subscribers[client_id] = int(subscriber_line[2])
                elif operation == 'UNSUB':
                    if client_id not in subscribers:
                        print(f"Warning when reading subscribers from topic '{topic_id}': UNSUB operation without any previous SUB operation")
                    else:
                        del subscribers[client_id]
                elif operation == 'UPDATE':
                    if client_id not in subscribers:
                        print(f"Error when reading subscribers from topic '{topic_id}': UPDATE operation without any previous SUB operation")
                        return None
                    else:
                        subscribers[client_id] = int(subscriber_line[2])
                else:
                    print(f"Invalid operation in subscribers file from topic '{topic_id}'")
                    return None
            except ValueError:
                print(f"Invalid client ID or last message received format (not int)")
                return None
        return subscribers

    def read_all_subscribers():
        if not pathlib.Path(TOPICS_DIR).exists():
            return {}

        subscribers = {}
        for topic in os.listdir(TOPICS_DIR):
            topic_subscribers = ServerIO.clean_subscribers(topic)
            if topic_subscribers == None:
                return None
            subscribers[topic] = topic_subscribers
        return subscribers

    def add_subscriber(topic_id, client_id, last_publication_received): 
        result, error_str = FileIO.append_line(f"{TOPICS_DIR}/{topic_id}/subscribers.csv", f"SUB,{client_id},{last_publication_received}")
        if not result:
            print(f"Error when appending subscription of client '{client_id}' to topic '{topic_id}': {error_str}")
        return result
    
    def remove_subscriber(topic_id, client_id):
        result, error_str = FileIO.append_line(f"{TOPICS_DIR}/{topic_id}/subscribers.csv", f"UNSUB,{client_id}")
        if not result:
            print(f"Error when appending unsubscription of client '{client_id}' to topic '{topic_id}': {error_str}")
        return result

    def update_subscriber(topic_id, client_id, last_publication_received):
        result, error_str = FileIO.append_line(f"{TOPICS_DIR}/{topic_id}/subscribers.csv", f"UPDATE,{client_id},{last_publication_received}")
        if not result:
            print(f"Error when appending update of client '{client_id}' subscription to topic '{topic_id}': {error_str}")
        return result

    # Garbage collection
    def clean_subscribers(topic_id):
        subscribers = ServerIO.read_subscribers(topic_id)
        if subscribers == None:
            return None
        
        result, error_str = FileIO.write_lines(f"{TOPICS_DIR}/{topic_id}/subscribers.csv", [f"SUB,{client_id},{last_publication_received}" for client_id, last_publication_received in subscribers.items()])
        if not result:
            print(f"Error when writing subcriptions of topic '{topic_id}': {error_str}")
            return None
        return subscribers

    # ============================= COUNTERS =============================
    
    def save_client_counter(client_id, counter):        
        result, error_str = FileIO.append_line(f"{SERVER_DIR}/client_counters.csv", f"{client_id},{counter}")
        if not result:
            print(f"Error when saving client counter of client '{client_id}': {error_str}")
        return result
    
    def read_client_counters():
        if not pathlib.Path(f"{SERVER_DIR}/client_counters.csv").exists():
            return {}
        
        result, lines = FileIO.read_lines(f"{SERVER_DIR}/client_counters.csv")
        if not result:
            print(f"Error when reading client counters: {lines}")
            return None
        
        client_counters = {}
        for i in range(len(lines)-1, -1, -1):
            line = lines[i].split(",")
            try:
                client_id, counter = line[0], int(line[1])
            except ValueError:
                print("Invalid client counter format (not int)")
                return None
            if client_id not in client_counters:
                client_counters[client_id] = counter
        return client_counters

    # Garbage collection
    def clean_client_counters():
        client_counters = ServerIO.read_client_counters()
        if client_counters == None:
            return None
        
        result, error_str = FileIO.write_lines(f"{SERVER_DIR}/client_counters.csv", [f"{client_id},{counter}" for client_id, counter in client_counters.items()])
        if not result:
            print(f"Error when writing client counters: {error_str}")
            return None
        return client_counters