from pexpect import spawn, EOF
from threading import Thread
import random
import time
import subprocess
import logging

TIMEOUT = 120

N_CLIENTS = 25
N_MESSAGES = 5
TOPICS = ['A', 'B', 'C', 'D', 'E']

# Subscribe to all available topics
def subscribe(p):
    for c in random.sample(TOPICS, len(TOPICS)): # Shuffle the order of topics
        while True:
            p.sendline(f'SUB topic{c}')
            index = p.expect([f'SUB successful, you are now subscribed to topic{c}', 'SUB failed*', 'CRASH'], timeout=TIMEOUT)
            if index == 0:
                break
            if index == 2:
                logging.error('Client crash')
                p.expect('Enter command:*')

# Each client should send N_MESSAGES across all topics
def put_msg(p):
    for i in range(N_MESSAGES):
        c = random.choice(TOPICS)
        while True:
            p.sendline(f'PUT topic{c} publication{i}')
            index = p.expect(['PUT successful', 'PUT failed with: Duplicated message', 'PUT failed with: Server is offline', 'CRASH'], timeout=TIMEOUT)
            if index == 0 or index == 1:
                break
            if index == 3:
                logging.error('Client crash')
                p.expect('Enter command:*')

# Get all the messages place on all topics
# Since N_CLIENTS each are writing messages publication0, publication1, ..., publication{N_MESSAGES-1}
# by counting the number of times each publication number (i.e publication0 -> 0, should be equal to N_CLIENTS) appears, 
# we can infer that no publication was lost
def get_msg(p):
    counts = {}
    for c in random.sample(TOPICS, len(TOPICS)):
        while True: # Read all messages in topic
            p.sendline(f'GET topic{c}')
            index = p.expect([f'Received: publication\d+', 'GET failed with: All publications from*', 'GET failed with: Server is offline', 'CRASH'], timeout=TIMEOUT)
            
            if index == 0:
                publication = p.after.decode('utf-8') # "Received: publicationN"
                publication_number = int(publication[21:])
                counts[publication_number] = counts.get(publication_number, 0) + 1 # If empty start with 0+1
            elif index == 1:
                break
            elif index == 3:
                logging.error('Client crash')
                p.expect('Enter command:*')
    
    for i in range(N_MESSAGES):
        if(counts[i] != N_CLIENTS):
            msg = f"Not all messages were received! Got {counts[i]} messages for publication{i}, expected {N_CLIENTS}"
            raise Exception(msg)

def unsub_msg(p):
    for c in random.sample(TOPICS, len(TOPICS)): # Shuffle the order of topics
        while True:
            p.sendline(f'UNSUB topic{c}')
            index = p.expect(['UNSUB successful*', 'UNSUB failed*', 'CRASH'], timeout=TIMEOUT)
            if index == 0:
                break
            if index == 2:
                logging.error('Client crash')
                p.expect('Enter command:*')


def distribute_op(processes, target):
    threads = []
    for p in processes:
        thread = Thread(target = target, args = (p, ))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

def main():
    with open('test/logs/server.log', 'wb') as file:
        server_process = subprocess.Popen(['python3', 'test/faulty_server.py'], stdout=file, stderr=file)
    processes = [spawn(f'python3 test/faulty_client.py test/data/client{i}') for i in range(N_CLIENTS)]
    distribute_op(processes, subscribe)
    time.sleep(10) # Make sure all SUB messages arrive before the first PUT (So we can count the number of publications correctly)
    distribute_op(processes, put_msg)
    time.sleep(10) # Wait for all PUT messages to arrive.
    distribute_op(processes, get_msg)
    server_process.kill()

if __name__ == '__main__':
    main()