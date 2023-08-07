# PUT sends (topicA, CLIENT_A_ID, CLIENT_COUNTER=0, msg)
# GET sends (topicA, CLIENT_ID, LAST_MESSAGE_RECEIVED or 0 if first GET)
# SUB sends (topicA, CLIENT_ID)
# UNSUB sends (topicA, CLIENT_ID)

# Message:
#   Header:
#   - type
#   - topic
#   - client_id
#   Body:
#   - client_counter
#   - last_message_received
#   - data

from enum import Enum
import json

class RequestType(str, Enum):
    GET = 'GET'
    PUT = 'PUT'
    SUB = 'SUB'
    UNSUB = 'UNSUB'
    REQUEST_ID = 'REQUEST_ID'

class Request:
    def __init__(self, request_type, topic, client_id, body):
        self._request_type = request_type
        self._topic = topic
        self._client_id = client_id
        self._body = body

    def from_json(request_json):
        request = json.loads(request_json)
        return Request(
            request['type'],
            request['topic'],
            request['client_id'],
            request['body']
        )
    
    def __str__(self):
        return json.dumps({
            'type': self._request_type,
            'topic': self._topic,
            'client_id': self._client_id,
            'body': self._body
        })


    @property
    def request_type(self):
        return self._request_type

    @request_type.setter
    def request_type(self, request_type):
        self._request_type = request_type

    @property
    def topic(self):
        return self._topic
    
    @topic.setter
    def topic(self, topic):
        self._topic = topic
    
    @property
    def client_id(self):
        return self._client_id

    @client_id.setter
    def client_id(self, client_id):
        self._client_id = client_id
    
    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, body):
        self._body = body
        
def create_get_request(topic, client_id, last_publication_received):
    return Request(RequestType.GET, topic, client_id, {'last_publication_id': last_publication_received})

def create_put_request(topic, client_id, client_counter, publication):
    return Request(RequestType.PUT, topic, client_id, {'counter': client_counter, 'publication': publication})

def create_subscribe_request(topic, client_id): 
    return Request(RequestType.SUB, topic, client_id, {})

def create_unsubscribe_request(topic, client_id):
    return Request(RequestType.UNSUB, topic, client_id, {})

def create_id_request():
    return Request(RequestType.REQUEST_ID, "", "", {})