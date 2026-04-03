import json
import hashlib
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet

class DSANTotem:
    def __init__(self, gesture_sequence=None):
        # Chaves de Assinatura e Criptografia
        self.sig_private = ed25519.Ed25519PrivateKey.generate()
        self.enc_private = x25519.X25519PrivateKey.generate()
        
        # O Gesto Soberano: Padrão [1, 2, 0] (Indicador, Médio, Polegar)
        self.unlock_gesture = gesture_sequence or [1, 2, 0] 

    def verify_gesture(self, input_sequence):
        """Validação física no SmartRing."""
        return input_sequence == self.unlock_gesture

    def get_public_keys(self):
        return {
            "sig": self.sig_private.public_key().public_bytes_raw().hex(),
            "enc": self.enc_private.public_key().public_bytes_raw().hex()
        }

    def generate_shared_key(self, peer_enc_pub_hex):
        """Cria o segredo compartilhado para E2EE (X25519)."""
        peer_pub_bytes = bytes.fromhex(peer_enc_pub_hex)
        peer_pub = x25519.X25519PublicKey.from_public_bytes(peer_pub_bytes)
        shared_secret = self.enc_private.exchange(peer_pub)
        
        # Derivação de chave AES segura
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'dsan-v1.2-e2ee',
        ).derive(shared_secret)
        
        return base64.urlsafe_b64encode(derived_key)
    
class DSANAgent:
    def __init__(self, agent_id):
        self.id = agent_id
        self.totem = DSANTotem()
        self.local_log = []
        self.state_hash = "0" * 64
        self.data_path = f"data/agents/{agent_id}.json"
        os.makedirs("data/agents", exist_ok=True)
        self.load_state()

    def encrypt_payload(self, recipient_enc_pub_hex, payload_dict):
        """Cifra o conteúdo para o destinatário."""
        shared_key = self.totem.generate_shared_key(recipient_enc_pub_hex)
        fernet = Fernet(shared_key)
        payload_json = json.dumps(payload_dict).encode()
        return fernet.encrypt(payload_json).decode()

    def decrypt_payload(self, sender_enc_pub_hex, encrypted_data):
        """Decifra o conteúdo vindo do remetente."""
        shared_key = self.totem.generate_shared_key(sender_enc_pub_hex)
        fernet = Fernet(shared_key)
        decrypted_json = fernet.decrypt(encrypted_data.encode())
        return json.loads(decrypted_json.decode())

    def sign_message(self, payload, recipient_pub_keys=None):
        """Cifra se houver chaves do destinatário, senão apenas assina."""
        final_payload = payload
        is_encrypted = False

        if recipient_pub_keys:
            final_payload = self.encrypt_payload(recipient_pub_keys['enc'], payload)
            is_encrypted = True

        envelope = {
            "sender_id": self.id,
            "payload": final_payload,
            "encrypted": is_encrypted,
            "sender_enc_pub": self.totem.get_public_keys()['enc']
        }
        
        envelope_json = json.dumps(envelope, sort_keys=True).encode()
        signature = self.totem.sig_private.sign(envelope_json).hex()
        return signature, envelope

    def receive(self, envelope, signature, sender_sig_pub_hex):
        """Valida, decifra (se necessário) e loga."""
        sender_sig_pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(sender_sig_pub_hex))
        envelope_json = json.dumps(envelope, sort_keys=True).encode()
        
        try:
            sender_sig_pub.verify(bytes.fromhex(signature), envelope_json)
            
            # Se estiver cifrado, decifra antes de salvar no log (ou salva cifrado para auditoria)
            data = envelope['payload']
            if envelope.get('encrypted'):
                data = self.decrypt_payload(envelope['sender_enc_pub'], data)
            
            self.log_event("MSG_ACCEPTED", {"from": envelope['sender_id'], "content": data})
            return True
        except Exception as e:
            print(f"Erro na recepção: {e}")
            return False

    def log_event(self, event_type, data):
        event = {
            "type": event_type,
            "prev_hash": self.state_hash,
            "data": data
        }
        event_json = json.dumps(event, sort_keys=True).encode()
        event_hash = hashlib.sha256(event_json).hexdigest()
        
        self.local_log.append({"hash": event_hash, "event": event})
        self.state_hash = event_hash
        self.save_state()

    def save_state(self):
        with open(self.data_path, 'w') as f:
            json.dump({"state_hash": self.state_hash, "log": self.local_log, "pub_keys": self.totem.get_public_keys()}, f, indent=4)

    def load_state(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                self.state_hash = data.get("state_hash", "0" * 64)
                self.local_log = data.get("log", [])