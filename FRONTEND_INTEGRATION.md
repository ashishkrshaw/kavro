# Frontend Integration

This doc explains how the encryption actually works in Kavro. I'm using my demo_client.py as reference since thats a working implementation.

## How messages get encrypted

The whole point of E2EE is that server never sees plaintext. So all encryption happens on the client side before sending.

I use NaCl (libsodium) for crypto. In Python thats pynacl, in JS its tweetnacl.

## Registration

Users need 8+ character password with at least 1 uppercase, 1 lowercase, and 1 number. I added these rules in schemas.py because weak passwords defeat the whole purpose.

```
POST /auth/register
{"username": "alice", "password": "AlicePass123"}
```

Returns an access_token for authenticated requests.

## Key generation

Each user generates a keypair on their device. In pynacl:

```python
from nacl.public import PrivateKey
priv = PrivateKey.generate()
pub = priv.public_key
```

The private key stays on device. Never send it anywhere. The public key gets uploaded to server so other users can encrypt messages to you.

## Publishing public key

I convert the public key to hex and send it:

```
POST /keys/publish
Headers: Authorization: Bearer <token>
{"identity_pubkey": "<hex>", "device_name": "my-phone"}
```

Server stores this. Anyone can fetch it to encrypt messages to this user.

## Sending a message

This is the interesting part. I don't use the identity keypair directly for each message. Instead I generate an ephemeral keypair per message.

```python
ephemeral_priv = PrivateKey.generate()
ephemeral_pub = ephemeral_priv.public_key

# create box with my ephemeral private + their identity public
box = Box(ephemeral_priv, recipient_public_key)
ciphertext = box.encrypt(message_bytes)
```

Then send the ciphertext and ephemeral public key:

```
POST /messages/
{
    "recipient_id": 123,
    "ciphertext": "<base64>",
    "ephemeral_pubkey": "<hex>"
}
```

## Receiving a message

Recipient fetches inbox, gets ciphertext and ephemeral_pubkey. They decrypt using their identity private key + senders ephemeral public key:

```python
box = Box(my_identity_private, sender_ephemeral_public)
plaintext = box.decrypt(ciphertext)
```

## Why ephemeral keys?

Forward secrecy. If someones identity key gets compromised later, old messages are still safe because each message used a different ephemeral key.

## Demo

Run client/demo_client.py to see full flow:

```
cd client
pip install requests pynacl
python demo_client.py
```

It does everything - registers users, exchanges keys, encrypts message, sends, fetches, decrypts.
