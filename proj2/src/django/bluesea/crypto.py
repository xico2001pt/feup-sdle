import os
from pathlib import Path
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
import pathlib

BASE_DIR = Path(__file__).resolve().parent.parent
PRIVATE_KEY_FILENAME = BASE_DIR / f"data/private_{os.getenv('BLUESEA_PORT')}.pem"
PUBLIC_KEY_FILENAME = BASE_DIR / f"data/public_{os.getenv('BLUESEA_PORT')}.pem"


def generate_keys_if_not_exists():
    if not (pathlib.Path(PRIVATE_KEY_FILENAME).exists() and pathlib.Path(PUBLIC_KEY_FILENAME).exists()): 
        generate()


def generate():
    key = RSA.generate(2048)
    
    private_key = key.export_key()
    file_out = open(PRIVATE_KEY_FILENAME, "wb")
    file_out.write(private_key)
    file_out.close()

    public_key = key.publickey().export_key()
    file_out = open(PUBLIC_KEY_FILENAME, "wb")
    file_out.write(public_key)
    file_out.close()


def get_keys():
    public_key = RSA.import_key(open(PUBLIC_KEY_FILENAME).read())
    private_key = RSA.import_key(open(PRIVATE_KEY_FILENAME).read())
    return public_key, private_key


def get_public_key():
    return RSA.import_key(open(PUBLIC_KEY_FILENAME).read())


def get_private_key():
    return RSA.import_key(open(PRIVATE_KEY_FILENAME).read())


def import_key_from_string(string):
    return RSA.import_key(key_from_string(string))


def key_from_string(string):
    return string.encode("iso-8859-1")


def key_to_string(key):
    return key.decode("iso-8859-1")


def sign_string(string):
    digest = SHA256.new()
    digest.update(string.encode('utf-8'))
    private_key = get_private_key()
    signer = PKCS1_v1_5.new(private_key)
    signature = signer.sign(digest)
    return signature


def verify_signature(public_key, string, signature):
    digest = SHA256.new()
    digest.update(string.encode('utf-8'))
    verifier = PKCS1_v1_5.new(public_key)
    verified = verifier.verify(digest, signature)
    return verified
