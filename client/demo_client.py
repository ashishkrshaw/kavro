# demo_client.py
# Requirements:
# pip install requests pynacl

import base64
import json
import os
import random
import logging
from pathlib import Path
import requests
from nacl.public import PrivateKey, PublicKey, Box
from nacl.encoding import HexEncoder

BASE_URL = "http://127.0.0.1:8000"  # change if your server is remote
TIMEOUT = 10

# configure logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("demo_client")

# Preset demo messages (one will be chosen randomly each run)
MESSAGES = [
    "Hello Bob! This is a secret message.",
    "Quick update: meeting at 10.",
    "Here's the OTP: 123456",
    "Lunch at 13:00?",
    "End-to-end encryption rocks \u2764\ufe0f"
]


def register(username, password):
    r = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["access_token"]


def login(username, password):
    r = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["access_token"]


def whoami(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("user_id")


def publish_key(token, identity_pubkey_hex, device_name="python-client"):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"identity_pubkey": identity_pubkey_hex, "device_name": device_name}
    r = requests.post(f"{BASE_URL}/keys/publish", json=payload, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_keys(user_id):
    r = requests.get(f"{BASE_URL}/keys/{user_id}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("devices", [])


def send_message(token, recipient_id, ciphertext_b64, ephemeral_pubkey_hex, metadata=None):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "recipient_id": recipient_id,
        "ciphertext": ciphertext_b64,
        "ephemeral_pubkey": ephemeral_pubkey_hex,
        "metadata": metadata or {}
    }
    r = requests.post(f"{BASE_URL}/messages/", json=payload, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def fetch_inbox(token, limit=20):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/messages/inbox?limit={limit}", headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("messages", [])


# crypto helpers
def gen_identity_keypair():
    priv = PrivateKey.generate()
    pub = priv.public_key
    return priv, pub


def keys_dir() -> Path:
    p = Path(__file__).parent / "keys"
    p.mkdir(exist_ok=True)
    return p


def save_identity_keys(username: str, priv: PrivateKey, pub: PublicKey) -> None:
    d = keys_dir()
    priv_hex = priv.encode(encoder=HexEncoder).decode()
    pub_hex = pub.encode(encoder=HexEncoder).decode()
    (d / f"{username}_priv.hex").write_text(priv_hex, encoding="utf-8")
    (d / f"{username}_pub.hex").write_text(pub_hex, encoding="utf-8")


def load_identity_keys(username: str):
    d = keys_dir()
    priv_file = d / f"{username}_priv.hex"
    pub_file = d / f"{username}_pub.hex"
    if priv_file.exists() and pub_file.exists():
        priv_hex = priv_file.read_text(encoding="utf-8").strip()
        pub_hex = pub_file.read_text(encoding="utf-8").strip()
        priv = PrivateKey(bytes.fromhex(priv_hex))
        pub = PublicKey(bytes.fromhex(pub_hex))
        return priv, pub
    return None


def identity_pubkey_to_hex(pub: PublicKey) -> str:
    return pub.encode(encoder=HexEncoder).decode()


def ephemeral_pubkey_to_hex(pub: PublicKey) -> str:
    return pub.encode(encoder=HexEncoder).decode()


def encrypt_for_recipient(ephemeral_priv: PrivateKey, recipient_pub_hex: str, plaintext: bytes):
    recipient_pub = PublicKey(bytes.fromhex(recipient_pub_hex))
    box = Box(ephemeral_priv, recipient_pub)
    ciphertext = box.encrypt(plaintext)  # returns nonce + ciphertext bytes
    return ciphertext  # raw bytes


def decrypt_for_recipient(recipient_priv: PrivateKey, ephemeral_pub_hex: str, ciphertext_b64: str):
    ephemeral_pub = PublicKey(bytes.fromhex(ephemeral_pub_hex))
    box = Box(recipient_priv, ephemeral_pub)
    ct = base64.b64decode(ciphertext_b64)
    return box.decrypt(ct)


def demo_flow():
    a_user = "alice_demo"
    b_user = "bob_demo"
    a_pass = "alicepass123"
    b_pass = "bobpass123"

    logger.info("Register/login users...")
    try:
        a_token = register(a_user, a_pass)
        logger.info("Alice registered.")
    except requests.HTTPError as e:
        logger.exception("Alice register failed; trying login")
        a_token = login(a_user, a_pass)
        logger.info("Alice logged in.")

    try:
        b_token = register(b_user, b_pass)
        logger.info("Bob registered.")
    except requests.HTTPError as e:
        logger.exception("Bob register failed; trying login")
        b_token = login(b_user, b_pass)
        logger.info("Bob logged in.")

    # Get numeric user ids from server
    alice_id = whoami(a_token)
    bob_id = whoami(b_token)
    print("Alice id:", alice_id, "Bob id:", bob_id)

    # load or generate identity keys locally (one per device)
    a_loaded = load_identity_keys(a_user)
    if a_loaded:
        a_priv, a_pub = a_loaded
    else:
        a_priv, a_pub = gen_identity_keypair()
        save_identity_keys(a_user, a_priv, a_pub)

    b_loaded = load_identity_keys(b_user)
    if b_loaded:
        b_priv, b_pub = b_loaded
    else:
        b_priv, b_pub = gen_identity_keypair()
        save_identity_keys(b_user, b_priv, b_pub)

    a_pub_hex = identity_pubkey_to_hex(a_pub)
    b_pub_hex = identity_pubkey_to_hex(b_pub)

    # publish identity public keys to the server
    print("Publish identity public keys...")
    publish_key(a_token, a_pub_hex, device_name="alice-py")
    publish_key(b_token, b_pub_hex, device_name="bob-py")
    print("Published keys.")

    # fetch published keys to verify and to obtain recipient identity key
    print("Fetch Bob keys from server (for encryption)...")
    devices = fetch_keys(bob_id)
    if not devices:
        raise RuntimeError("No devices for recipient found; publish step may have failed")
    recipient_identity_pub_hex = devices[0]["identity_pubkey"]
    print("Bob's identity pub (hex):", recipient_identity_pub_hex)

    # alice encrypts message for bob using ephemeral key
    ephemeral_priv = PrivateKey.generate()
    ephemeral_pub = ephemeral_priv.public_key
    ephemeral_hex = ephemeral_pub.encode(encoder=HexEncoder).decode()

    # choose a random message from the preset list
    chosen = random.choice(MESSAGES)
    message_text = chosen.encode("utf-8")
    ciphertext_bytes = encrypt_for_recipient(ephemeral_priv, recipient_identity_pub_hex, message_text)
    ciphertext_b64 = base64.b64encode(ciphertext_bytes).decode()

    # alice sends message to bob (recipient_id is numeric id)
    print("Alice sending encrypted message to Bob...")
    send_resp = send_message(a_token, bob_id, ciphertext_b64, ephemeral_hex, metadata={"topic": "demo"})
    print("Send response:", send_resp)

    # bob fetches inbox and decrypts messages
    print("Bob fetching inbox...")
    msgs = fetch_inbox(b_token)
    print("Inbox messages:", json.dumps(msgs, indent=2))

    if not msgs:
        print("No messages found in bob's inbox")
        return

    # decrypt the most recent (assume first)
    latest = msgs[0]
    # Debug: verify server returned the same ciphertext we sent (first message)
    try:
        if latest["ciphertext"] == ciphertext_b64:
            print("DEBUG: server ciphertext matches sent ciphertext")
        else:
            print("DEBUG: server ciphertext does NOT match sent ciphertext")
    except Exception:
        pass
    try:
        decrypted = decrypt_for_recipient(b_priv, latest["ephemeral_pubkey"], latest["ciphertext"])
        print("Decrypted plaintext:", decrypted.decode())
    except Exception as e:
        print("Failed to decrypt message:", e)
        print("Make sure ephemeral_pubkey and ciphertext are in the correct format.")

if __name__ == "__main__":
    demo_flow()
