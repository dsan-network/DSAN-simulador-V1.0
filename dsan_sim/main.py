# main.py
import time
from dsan_sim import DSANAgent, DSANSimulator

def run_simulation():
    print("=== DSAN MISSION CONTROL - V1.1 ===")
    
    # 1. Setup da Rede
    alice = DSANAgent("alice")
    bob = DSANAgent("bob")
    charlie = DSANAgent("charlie")
    
    # Criamos o simulador com 10% de chance de queda de pacotes
    sim = DSANSimulator(agents=[alice, bob, charlie], network_loss=0.1)
    
    # 2. Execução de Fluxo Legítimo
    print("\n--- INICIANDO TRANSMISSÃO LEGÍTIMA ---")
    sim.send_message("alice", "bob", {"type": "ORDEM_COMPRA", "item": "Soberania", "qtd": 1})
    sim.send_message("bob", "charlie", {"type": "LOGÍSTICA", "status": "EM_TRANSITO"})

    # 3. CENÁRIO DE ATAQUE: Replay Attack
    # Vamos capturar manualmente uma mensagem válida e tentar reenviá-la
    print("\n--- TESTE DE SEGURANÇA: REPLAY ATTACK ---")
    # Alice assina uma mensagem
    sig, envelope = alice.sign_message({"type": "SAQUE", "valor": 1000})
    
    print("Tentativa 1 (Original):")
    bob.receive(envelope, sig, alice.public_key_bytes) # Deve aceitar
    
    print("Tentativa 2 (Replay da mesma mensagem por um atacante):")
    # O sistema de Nonce/Timestamp no agent.py deve bloquear isso
    success = bob.receive(envelope, sig, alice.public_key_bytes)
    if not success:
        print("🛡️ SUCESSO: Sistema anti-replay bloqueou a duplicata.")

    # 4. CENÁRIO DE ATAQUE: Impersonificação (Sybil)
    print("\n--- TESTE DE SEGURANÇA: IMPERSONIFICAÇÃO ---")
    atacante = DSANAgent("hacker")
    # O hacker tenta enviar uma mensagem dizendo que é a 'alice'
    sig_fake, env_fake = atacante.sign_message({"type": "COMANDO", "cmd": "FORMAT_C"})
    env_fake["sender_id"] = "alice" # Fraude no ID
    
    # Bob tenta validar usando a chave da Alice (que ele pegaria no Registry)
    success_fake = bob.receive(env_fake, sig_fake, alice.public_key_bytes)
    if not success_fake:
        print("🛡️ SUCESSO: Assinatura do hacker não confere com a chave pública da Alice.")

    # 5. Relatório de Integridade (Hash Chaining)
    print("\n--- AUDITORIA FINAL DE ESTADO (HASH CHAIN) ---")
    for agent in [alice, bob, charlie]:
        proof = agent.get_state_proof()
        print(f"Agente {agent.id}:")
        print(f"  > Log Height: {proof['log_height']} eventos")
        print(f"  > State Hash: {proof['state_hash']}")

if __name__ == "__main__":
    run_simulation()
