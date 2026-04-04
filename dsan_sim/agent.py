import json
import hashlib
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet

class DSANTotem:
    def __init__(self, sig_priv_hex=None, enc_priv_hex=None):
        if sig_priv_hex and enc_priv_hex:
            self.sig_private = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(sig_priv_hex))
            self.enc_private = x25519.X25519PrivateKey.from_private_bytes(bytes.fromhex(enc_priv_hex))
        else:
            self.sig_private = ed25519.Ed25519PrivateKey.generate()
            self.enc_private = x25519.X25519PrivateKey.generate()
        self.unlock_gesture = [1, 2, 0]

    def verify_gesture(self, input_sequence):
        return input_sequence == self.unlock_gesture

    def get_public_keys(self):
        return {
            "sig": self.sig_private.public_key().public_bytes_raw().hex(),
            "enc": self.enc_private.public_key().public_bytes_raw().hex()
        }

    def export_private_keys(self):
        return {
            "sig": self.sig_private.private_bytes_raw().hex(),
            "enc": self.enc_private.private_bytes_raw().hex()
        }

    def generate_shared_key(self, peer_enc_pub_hex):
        peer_pub = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(peer_enc_pub_hex))
        shared_secret = self.enc_private.exchange(peer_pub)
        derived_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b'dsan-v1.2-e2ee').derive(shared_secret)
        return base64.urlsafe_b64encode(derived_key)

class DSANAgent:
    def __init__(self, agent_id):
        self.id = agent_id
        self.data_path = f"data/agents/{agent_id}.json"
        os.makedirs("data/agents", exist_ok=True)
        self.local_log = []
        self.state_hash = "0" * 64
        self.totem = None
        if not self.load_state():
            self.totem = DSANTotem()
            self.save_state()

    def sign_message(self, payload, recipient_pub_keys=None):
        final_payload = payload
        is_encrypted = False
        if recipient_pub_keys:
            shared_key = self.totem.generate_shared_key(recipient_pub_keys['enc'])
            final_payload = Fernet(shared_key).encrypt(json.dumps(payload).encode()).decode()
            is_encrypted = True

        envelope = {
            "encrypted": is_encrypted,
            "payload": final_payload,
            "sender_enc_pub": self.totem.get_public_keys()['enc'],
            "sender_id": self.id
        }
        # Assinamos apenas o payload para evitar erros de formatação JSON na rede
        signature = self.totem.sig_private.sign(final_payload.encode()).hex()
        return signature, envelope

    def receive(self, envelope, signature, sender_sig_pub_hex):
        try:
            sender_sig_pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(sender_sig_pub_hex))
            sender_sig_pub.verify(bytes.fromhex(signature), envelope['payload'].encode())
            data = envelope['payload']
            if envelope.get('encrypted'):
                shared_key = self.totem.generate_shared_key(envelope['sender_enc_pub'])
                data = json.loads(Fernet(shared_key).decrypt(data.encode()).decode())
            return True
        except:
            return False

    def save_state(self):
        with open(self.data_path, 'w') as f:
            json.dump({
                "state_hash": self.state_hash,
                "log": self.local_log,
                "priv_keys": self.totem.export_private_keys()
            }, f, indent=4)

    def load_state(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                priv = data.get("priv_keys")
                if priv:
                    self.totem = DSANTotem(sig_priv_hex=priv['sig'], enc_priv_hex=priv['enc'])
                    return True
        return False