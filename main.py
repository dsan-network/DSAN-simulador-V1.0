from dsan_sim import DSANAgent, DSANSimulator

def run():
    alice = DSANAgent("alice")
    bob = DSANAgent("bob")
    sim = DSANSimulator([alice, bob], network_loss=0.1)
    
    print("--- Teste de Mensagem ---")
    sim.send_message("alice", "bob", {"cmd": "hello"})
    
    print("\n--- Auditoria Final ---")
    print(f"Alice: {alice.get_state_proof()['state_hash'][:16]}")
    print(f"Bob:   {bob.get_state_proof()['state_hash'][:16]}")

if __name__ == "__main__":
    run()
