from client import Client
import argparse
import logging

logging.disable()

parser = argparse.ArgumentParser(description='Client for the server')
parser.add_argument('client_data_dir', help='Directory where client data should be stored', type=str)
parser.add_argument('-v', '--verbose', help='Verbose output', action='store_true')

def main():
    args = parser.parse_args()
 
    try: 
        client = Client(args.client_data_dir)
    except Exception as e: 
        print(e)
        exit(1)
    
    if args.verbose:
        print_help()
        print_topics_subscribed(client)
    
    while True:
        command = input('Enter command: ')
        execute_command(client, command)

def print_topics_subscribed(client): 
    print("You are subscribed to the following topics:")
    topics = client.last_publications_read.keys()
    print(", ".join(topic for topic in topics) if len(topics) > 0 else "None")

def print_help():
    print("Available commands:")
    print("  GET topic_id")
    print("  PUT topic_id publication")
    print("  SUB topic_id")
    print("  UNSUB topic_id")
    print("  EXIT")

def execute_command(client, command):
    split_command = command.split(" ")
    operation = split_command[0]

    if operation == "EXIT":
        print("Exiting...")
        exit(0)

    topic_id = split_command[1]

    if operation == "GET":
        succ, publication = client.get(topic_id)
        print(f"Received: {publication}" if succ else f"GET failed with: {publication}")
    elif operation == "PUT":
        publication = " ".join(split_command[2:])
        succ, error = client.put(topic_id, publication)
        print("PUT successful" if succ else f"PUT failed with: {error}")
    elif operation == "SUB":
        succ, error = client.subscribe(topic_id)
        print(f"SUB successful, you are now subscribed to {topic_id}" if succ else f"SUB failed with: {error}")
    elif operation == "UNSUB":
        succ, error = client.unsubscribe(topic_id)
        print(f"UNSUB successful, you are now unsubscribed from {topic_id}" if succ else f"UNSUB failed with: {error}")
    else:
        print(f"Operation {operation} not recognized")

if __name__ == "__main__":
    main()