import hashlib
import time
import json
import os
from typing import List, Dict, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

class DSANTotem:
    """Hardware Root of Trust - Gera e protege chaves Ed25519."""
    def __init__(self):
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self._private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

class DSANAgent:
    def __init__(self, agent_id: str, storage_dir: str = "data/agents"):
        self.id = agent_id
        # Garante que a pasta de dados existe
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)
            
        self.storage_path = os.path.join(storage_dir, f"{agent_id}.json")
        
        # Inicializa o Totem (Identidade)
        self.totem = DSANTotem()
        self.public_key_bytes = self.totem.public_key_bytes
        
        # Estado Interno
        self.inbox: List[Dict] = []
        self.local_log: List[Dict] = []
        self.state_hash = b"\x00" * 32
        self.last_nonces: Dict[str, float] = {}

        # Tenta restaurar estado anterior
        self.load_state()

    def _canonical_pack(self, msg: Dict[str, Any]) -> bytes:
        """Gera JSON determinístico para assinatura/hashing."""
        return json.dumps(msg, sort_keys=True, separators=(',', ':')).encode()

    def save_state(self):
        """Persiste o log e hash no disco."""
        state_data = {
            "state_hash": self.state_hash.hex(),
            "last_nonces": self.last_nonces,
            "local_log": self.local_log,
            "public_key": self.public_key_bytes.hex()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(state_data, f, indent=4)

    def load_state(self):
        """Recupera estado do disco se disponível."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.state_hash = bytes.fromhex(data["state_hash"])
                    self.last_nonces = data["last_nonces"]
                    self.local_log = data["local_log"]
                return True
            except:
                return False
        return False

    def sign_message(self, payload: Dict[str, Any]):
        envelope = {"payload": payload, "nonce": time.time(), "sender_id": self.id}
        signature = self.totem.sign(self._canonical_pack(envelope))
        return signature, envelope

    def receive(self, envelope: Dict, signature: bytes, sender_pubkey: bytes) -> bool:
        try:
            sender_id = envelope.get("sender_id")
            nonce = envelope.get("nonce", 0)
            
            # Anti-Replay
            if sender_id in self.last_nonces and nonce <= self.last_nonces[sender_id]:
                return False 
            
            # Verificação Criptográfica
            sender_key = ed25519.Ed25519PublicKey.from_public_bytes(sender_pubkey)
            sender_key.verify(signature, self._canonical_pack(envelope))
            
            self.last_nonces[sender_id] = nonce
            self.log_event("MSG_ACCEPTED", {"from": sender_id, "payload": envelope['payload']})
            return True
        except:
            return False

    def log_event(self, event_type: str, data: Any):
        """Encadeia eventos e salva no disco."""
        event = {"type": event_type, "data": data, "prev_hash": self.state_hash.hex()}
        event_hash = hashlib.sha256(self._canonical_pack(event)).digest()
        
        self.local_log.append({"event": event, "hash": event_hash.hex()})
        self.state_hash = hashlib.sha256(self.state_hash + event_hash).digest()
        
        self.save_state()

    def get_state_proof(self) -> Dict:
        return {
            "agent_id": self.id, 
            "state_hash": self.state_hash.hex(), 
            "log_height": len(self.local_log)
        }