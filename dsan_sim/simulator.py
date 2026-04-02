import random
import time
from typing import List, Dict
from dsan_sim.agent import DSANAgent

class DSANSimulator:
    """
    Simulador DSAN v1.1.
    Suporta: Envelopes assinados, Proteção anti-replay e Verificação de Identidade.
    """
    
    def __init__(self, agents: List[DSANAgent], network_loss: float = 0.1):
        # Mapeia ID -> Objeto Agente (Simula a visibilidade da rede P2P)
        self.agents = {agent.id: agent for agent in agents}
        self.network_loss = network_loss
        self.time_step = 0

    def send_message(self, sender_id: str, receiver_id: str, payload: dict):
        """
        Orquestra o envio soberano:
        1. Remetente assina o payload (gera envelope + sig)
        2. Simulador aplica perda de pacotes
        3. Receptor valida usando a PubKey do remetente
        """
        if sender_id not in self.agents or receiver_id not in self.agents:
            print(f"❌ Erro: Agente {sender_id} ou {receiver_id} não encontrado.")
            return

        sender = self.agents[sender_id]
        receiver = self.agents[receiver_id]

        # --- Camada de Aplicação (Agente) ---
        # O agente gera o envelope com nonce e assina via Totem
        signature, envelope = sender.sign_message(payload)

        # --- Camada de Rede (Simulador) ---
        if random.random() < self.network_loss:
            print(f"💥 REDE: Mensagem de {sender_id} para {receiver_id} foi DROPPADA.")
            return

        # --- Camada de Recepção (Verificação) ---
        # O receptor recebe o envelope e a assinatura.
        # Ele precisa da Chave Pública do remetente (simulando busca no BotRegistry/Blockchain)
        success = receiver.receive(
            envelope=envelope, 
            signature=signature, 
            sender_pubkey=sender.public_key_bytes
        )

        if success:
            print(f"✅ SUCESSO: {sender_id} -> {receiver_id} | Type: {payload.get('type')}")
        else:
            print(f"🛡️ REJEITADO: {receiver_id} negou msg de {sender_id} (Assinatura Inválida ou Replay)")

    def run(self, steps: int = 5):
        """Executa um ciclo de teste básico."""
        print(f"🌐 DSAN-Sim v1.1 iniciado com {len(self.agents)} agentes.")
        print(f"📡 Network Loss: {self.network_loss*100}% | Proteção Anti-Replay: Ativa\n")
        
        for step in range(steps):
            self.time_step = step
            # Exemplo: alice envia para todos
            if 'alice' in self.agents:
                for target_id in self.agents:
                    if target_id != 'alice':
                        self.send_message(
                            'alice', 
                            target_id, 
                            {"type": "PING", "step": step}
                        )
            time.sleep(0.1)

        print("\n📊 Relatório de Integridade Final:")
        for aid, agent in self.agents.items():
            proof = agent.get_state_proof()
            print(f"  Agente [{aid}]: Hash={proof['state_hash'][:16]}... | Eventos={proof['log_height']}")
