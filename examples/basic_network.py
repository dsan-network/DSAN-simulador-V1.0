# exemplos/basic_network.py
from dsan_sim import DSANAgent, DSANSimulator

def run_demo():
    print("--- DSAN NETWORK DEMO ---")
    agents = [DSANAgent(f"node_{i}") for i in range(5)]
    sim = DSANSimulator(agents, network_loss=0.05)
    
    # Todos mandam um PING para o node_0
    for i in range(1, 5):
        sim.send_message(f"node_{i}", "node_0", {"msg": "Hello DSAN"})
    
    print("\nEstado Final do Node_0:")
    print(agents[0].get_state_proof())

if __name__ == "__main__":
    run_demo()
