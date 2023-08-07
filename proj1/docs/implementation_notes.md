# Proposed solution

Based on the [Lazy Pirate](https://zguide.zeromq.org/docs/chapter4/#Client-Side-Reliability-Lazy-Pirate-Pattern) pattern.


## DOUBTS 

- How to define message ids? Who has that responsibility, the client or the server at the time of reception? Depending on whose, how should that id be created? (timestamp, hash + something, something related to the topic, maybe IP and port)? 
- How do we avoid the scenario where garbage collection for topic deletion does not know if a message has been read
- Very large messages, should we use multipart?
- Should we ensure that every client has a unique ID?
- Should we take special measures when clients have the same ID? For example, should we implement some form of authentication system using passwords or encryption key pairs to avoid problems? In our current 

python3 cli.py data

```
mensagem1
mensagem2
SUB -> ACK(2) -- client doesn't receive this ACK
mensagem3
mensagem4
SUB -> ACK(2) or ACK(4) 
```

## CLI Commands

To start the cli application: `python main.py`

This executable reads from the stdin the following commands: 

- `GET   <TOPIC ID>`
    - This command must present an error if the client isn't subscribed to the topic with ID received

- `PUT   <TOPIC ID> <DATA>` (maybe multiple files in the future)
    - Returns error if the topic does not exist 
    - Logs the request for fault tolerance

- `SUB   <TOPIC ID>`
    - A client can subscribe multiple topics (it should save them in persistent storage)
    
- `UNSUB <TOPIC ID>`

## Messages Client <=> Server

### GET

Information sent: TOPIC_ID, LAST_MESSAGE_RECEIVED_ID

Reply: ACK(MESSAGE_ID, )

### PUT

Information sent: TOPIC_ID, 

Reply: ...

### SUB

Information sent: TOPIC_ID, 

Reply: ...

### UNSUB 

Information sent: TOPIC_ID, 

Reply: ...


## Execution Example

Stores for (CLIENT_ID, LAST_MESSAGE_RECEIVED) and (CLIENT_ID, CLIENT_COUNTER) must check for preexisting entries.

CLIENT_ID = HASH(IP:PORT), or use private keys 
CLIENT_COUNTER = Operation counter, increments everytime the client receives an response (PUT, SUB) from the server (?). Also increases when client gives up while sending a message (PUT, SUB).

### SUB

Alternative A.
```
[client:A] SUB topicA 
[client:A] sends (topicA, CLIENT_ID, CLIENT_COUNTER=0)
[server] verifies existence (topicA, CLIENT_ID, CLIENT_COUNTER, OLD_LAST_MESSAGE_IN_TOPIC) -- OLD_LAST_MESSAGE_IN_TOPIC is useful for when client doens't receive ACK, it will receive messages from the first SUB he does (the one that failed)
-- exists
[server] ACK(OLD_LAST_MESSAGE_IN_TOPIC)
-- does not exist
[server] stores (topicA, CLIENT_ID, CLIENT_COUNTER, LAST_MESSAGE_IN_TOPIC)
[server] send ACK(LAST_MESSAGE_IN_TOPIC)
[server] verifies (CLIENT_ID, CLIENT_COUNTER)
```

Alternative B.
```
[client:A] SUB topicA 
[client:A] sends (topicA, CLIENT_ID)
[server] stores (topicA, CLIENT_ID)
[server] sends ACK(LAST_MESSAGE_IN_TOPIC)
```

### PUT

```
[client:A] PUT topicA msg
[client:A] sends (topicA, CLIENT_COUNTER=0, CLIENT_A_ID, msg)
[server] verifies (topicA, CLIENT_A_ID CLIENT_COUNTER=0)
    []
-- server does not have (CLIENT_A_ID, CLIENT_COUNTER=0)
[server] stores msg with id=1
    [topicA{1:msg}]
[server] stores (topicA, CLIENT_A_ID, CLIENT_COUNTER=0)
    [(topicA, CLIENT_A_ID, 0)]
-- error: server doens't send ACK, so client tries again
[client:A] PUT topicA msg
[client:A] sends (topicA, CLIENT_COUNTER=0, CLIENT_A_ID, msg)
[server] verifies (topicA, CLIENT_A_ID, CLIENT_COUNTER=0)
    [(topicA, CLIENT_A_ID, 0)]
-- server has (topicA, CLIENT_A_ID, CLIENT_COUNTER=0), occurance of a repeated message
[server] sends ACK(CLIENT_COUNTER=0)
-- or ACK(MESSAGE_ALREADY_RECEIVED)
[client:A] receives ACK(CLIENT_COUNTER=0) and increments CLIENT_COUNTER

[client:B] PUT topicA another_msg
[client:B] sends (topicA, CLIENT_COUNTER=0, CLIENT_B_ID, another_msg)
[server] verifies (CLIENT_B_ID, CLIENT_COUNTER=0)
    [(topicA, CLIENT_A_ID, 0)]
-- server does not have (topicA, CLIENT_B_ID, CLIENT_COUNTER=0)
[server] stores another_msg with id=2
    [topicA{1:msg, 2:another_msg}]
[server] stores (topicA, CLIENT_B_ID, CLIENT_COUNTER=0)
    [(topicA, CLIENT_A_ID, 0), (topicA, CLIENT_B_ID, 0)]
[server] sends ACK(CLIENT_COUNTER=0)
[client:B] receives ACK(CLIENT_COUNTER=0) and increments CLIENT_COUNTER

[client:B] PUT topicA another_another_msg
[client:B] sends (topicA, CLIENT_COUNTER=1, CLIENT_B_ID, another_another_msg)
[server] verifies (topicA, CLIENT_B_ID, CLIENT_COUNTER=1)
    [(topicA, CLIENT_A_ID, 0), (topicA, CLIENT_B_ID, 0)]
-- server does not have (topicA, CLIENT_B_ID, CLIENT_COUNTER=1)
[server] stores another_msg with id=3
    [topicA{1:msg, 2:another_msg, 3:another_another_msg}]
[server] stores (topicA, CLIENT_B_ID, CLIENT_COUNTER=1)
    [(topicA, CLIENT_A_ID, 0), (topicA, CLIENT_B_ID, 1)]
[server] sends ACK(CLIENT_COUNTER=1)
[client:B] receives ACK(CLIENT_COUNTER=1) and increments CLIENT_COUNTER
```

### GET

```
[client:B] GET topicA
[client:B] sends (topicA, CLIENT_ID, LAST_MESSAGE_RECEIVED or 0 if first GET)
[server] stores (topicA, CLIENT_ID, LAST_MESSAGE_RECEIVED) -- for garbage collecting
[server] finds first message with MESSAGE_ID > LAST_MESSAGE_RECEIVED
-- server finds message
[server] sends ACK(message, MESSAGE_ID)
[client:B] receives ACK and changes LAST_MESSAGE_RECEIVED=MESSAGE_ID
-- server does not find the message
[server] sends ACK(NO_MESSAGES_LEFT_TO_READ)
*** Client sends new GET requests until NO_MESSAGES_LEFT_TO_READ is returned ***
```

## Server "class" 

Attributes: 
- ZMQ socket


Stores (persitent files, possible json [?]):
- (topicA, CLIENT_ID) for SUB
- (topicA, CLIENT_ID, CLIENT_COUNTER) for PUT
- (topicA, CLIENT_ID, LAST_MESSAGE_RECEIVED) for Garbage Collector
- Topic queues [topic: {id: text}]


## Next steps 

1. Lazy pirate send/receive interface 
    - Test lazy pirate send/receive
2. Message, with parsing and creation functions (for each operation, os ACKS)
3. CLI interface
4. Server state (check which is the best file structure for tuple storage, file handling, file search), possibly a cargo can be used - General struct
5. Client state, file handling (counter) and general struct
6. Communication (Client <-> Server operation)
    - PUT 
    - GET 
    - SUB
    - UNSUB 
7. Server Garbage Collection