import hashlib
import time
import json
from typing import List, Dict, Any, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

class DSANTotem:
    """
    Abstração do Hardware Root of Trust (ESP32-S3 / CM4).
    O Agente solicita assinaturas ao Totem, mas não possui a chave privada.
    """
    def __init__(self):
        # Em produção, isso estaria dentro do elemento seguro do hardware
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self._private_key.public_key()
        self.public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def sign(self, data: bytes) -> bytes:
        return self._private_key.sign(data)

class DSANAgent:
    """
    Agente Soberano DSAN Refatorado (v1.1-sim).
    Implementa serialização determinística e proteção contra replay.
    """
    def __init__(self, agent_id: str):
        self.id = agent_id
        self.totem = DSANTotem()
        self.public_key_bytes = self.totem.public_key_bytes
        
        self.inbox: List[Dict] = []
        self.local_log: List[Dict] = []
        self.state_hash = b"\x00" * 32
        
        # Controle de Replay: guarda o último nonce/timestamp de cada remetente
        self.last_nonces: Dict[str, float] = {}

    def _canonical_pack(self, msg: Dict[str, Any]) -> bytes:
        """Gera uma representação JSON estrita e ordenada para assinatura."""
        return json.dumps(msg, sort_keys=True, separators=(',', ':')).encode()

    def sign_message(self, payload: Dict[str, Any]) -> bytes:
        """Adiciona metadados de segurança e assina via Totem."""
        envelope = {
            "payload": payload,
            "nonce": time.time(), # No simulador usamos timestamp como nonce
            "sender_id": self.id
        }
        return self.totem.sign(self._canonical_pack(envelope)), envelope

    def verify_message(self, envelope: Dict, signature: bytes, sender_pubkey: bytes) -> bool:
        """Verifica integridade, autenticidade e frescor (anti-replay)."""
        try:
            # 1. Verificar se o nonce é antigo (Replay Attack)
            sender_id = envelope.get("sender_id")
            nonce = envelope.get("nonce", 0)
            if sender_id in self.last_nonces and nonce <= self.last_nonces[sender_id]:
                return False 

            # 2. Verificar assinatura criptográfica
            sender_key = ed25519.Ed25519PublicKey.from_public_bytes(sender_pubkey)
            sender_key.verify(signature, self._canonical_pack(envelope))
            
            # 3. Atualizar último nonce visto
            self.last_nonces[sender_id] = nonce
            return True
        except Exception:
            return False

    def receive(self, envelope: Dict, signature: bytes, sender_pubkey: bytes) -> bool:
        """Processa a mensagem e atualiza a hash-chain de estado."""
        if not self.verify_message(envelope, signature, sender_pubkey):
            self.log_event("SECURITY_ALERT", {"reason": "invalid_sig_or_replay", "from": envelope.get("sender_id")})
            return False
        
        event_data = {
            "action": "RECEIVE",
            "envelope": envelope,
            "system_time": time.time()
        }
        self.inbox.append(event_data)
        self.log_event("MSG_ACCEPTED", event_data)
        return True

    def log_event(self, event_type: str, data: Any):
        """Encadeamento de hashes para auditoria (Hash-Chaining)."""
        event = {
            "type": event_type,
            "data": data,
            "prev_hash": self.state_hash.hex()
        }
        
        # Serialização rigorosa do evento para o log
        event_bytes = self._canonical_pack(event)
        event_hash = hashlib.sha256(event_bytes).digest()
        
        self.local_log.append({"event": event, "hash": event_hash.hex()})
        # Novo state_hash depende do anterior + atual
        self.state_hash = hashlib.sha256(self.state_hash + event_hash).digest()

    def get_state_proof(self) -> Dict:
        return {
            "agent_id": self.id,
            "state_hash": self.state_hash.hex(),
            "log_height": len(self.local_log),
            "identity_key": self.public_key_bytes.hex()
        }
