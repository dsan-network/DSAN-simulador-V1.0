import sys
from flask import Flask, request, jsonify
from dsan_sim.agent import DSANAgent

app = Flask(__name__)

agent_name = sys.argv[1] if len(sys.argv) > 1 else "node_default"
bob = DSANAgent(agent_name)

@app.route('/')
def home():
    return f"Nó DSAN de {agent_name} ativo."

@app.route('/receive', methods=['POST'])
def receive():
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "Dados inválidos"}), 400

    envelope = data.get('envelope')
    signature = data.get('signature')
    sender_sig_pub = data.get('sender_sig_pub')

    success = bob.receive(envelope, signature, sender_sig_pub)

    if success:
        print(f"\n🔔 [NOVA MENSAGEM] O Totem de {bob.id} validou e decifrou o pacote!")
        return jsonify({"status": "Mensagem recebida e registrada no Ledger"}), 200
    else:
        print(f"\n❌ [ALERTA] Falha na validação criptográfica!")
        return jsonify({"status": "Falha na validação criptográfica"}), 400

if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
    print(f"\n==================================================")
    print(f"🛡️  NÓ SOBERANO DSAN: {agent_name.upper()}")
    print(f"📡 Escutando na porta {port}...")
    print(f"==================================================\n")
    app.run(host='127.0.0.1', port=port) # Mudamos de 0.0.0.0 para 127.0.0.1