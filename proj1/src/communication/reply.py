# GET:
#   NAK -> NO_MESSAGES_LEFT_TO_READ
#   ACK(message, MESSAGE_ID)
# SUB:
#   ACK(LAST_MESSAGE_IN_TOPIC)
# PUT:
#   ACK(CLIENT_COUNTER)
#   NAK 
# UNSUB: 
#   ACK

from enum import Enum
import json

class ReplyType(str, Enum):
    ACK = 'ACK',
    NAK = 'NAK'

class Reply: 
    def __init__(self, reply_type, body=None): 
        self._reply_type = reply_type
        self._body = body
    
    def from_json(reply_json):
        reply = json.loads(reply_json)
        return Reply(
            reply['type'],
            reply.get('body', None)
        )
        
    def __str__(self):
        d = {'type': self._reply_type}
        if self._body:
            d['body'] = self._body  
        return json.dumps(d)

    @property
    def reply_type(self):
        return self._reply_type

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @reply_type.setter
    def reply_type(self, value):
        self._reply_type = value

def create_get_ack(publication, publication_id):
    return Reply(ReplyType.ACK, {'publication': publication, 'publication_id': publication_id})

def create_empty_get_ack(): 
    return Reply(ReplyType.ACK, {'publication_id': -1})

def create_sub_ack(last_publication):
    return Reply(ReplyType.ACK, {'last_publication_id': last_publication})

def create_unsub_ack():
    return Reply(ReplyType.ACK, {})

def create_put_ack(counter):
    return Reply(ReplyType.ACK, {'current_publication_id': counter})

def create_nak(error_message=""):
    return Reply(ReplyType.NAK, {"error_message": error_message})

def create_id_ack(id):
    return Reply(ReplyType.ACK, {'id': id})

if __name__ == '__main__':
    d = {
        'type': ReplyType.ACK
    }
    print(Reply.from_json(json.dumps(d)))