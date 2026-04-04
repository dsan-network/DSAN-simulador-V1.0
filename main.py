import requests
import click
import json
from dsan_sim.agent import DSANAgent

session_agents = {}

def get_agent(name):
    """Carrega o agente garantindo que ele use o arquivo do disco."""
    agent = DSANAgent(name)
    # Força o carregamento do estado (chaves e log) do arquivo data/agents/name.json
    agent.load_state() 
    return agent

@click.group()
def cli():
    """🛡️ DSAN Sovereign Console - v1.3"""
    pass

@cli.command()
@click.argument('sender_id')
@click.argument('receiver_id')
@click.argument('msg')
@click.option('--port', default=5001, help="Porta de rede")
def send(sender_id, receiver_id, msg, port):
    """Teletransporta mensagem via rede real."""
    alice = get_agent(sender_id)
    bob = get_agent(receiver_id) 
    
    click.secho(f"\n--- 💍 AGUARDANDO TOTEM ({sender_id.upper()}) ---", fg='yellow', bold=True)
    gesture_input = click.prompt("Digite a sequência gestual", type=str)
    gesture_list = [int(d) for d in gesture_input]

    if not alice.totem.verify_gesture(gesture_list):
        click.secho("❌ ERRO: Gesto incorreto!", fg='red', bold=True)
        return

    # 1. Cifragem e Assinatura
    payload = {"type": "DREX_TRANSF", "content": msg}
    receiver_keys = bob.totem.get_public_keys()
    signature, envelope = alice.sign_message(payload, recipient_pub_keys=receiver_keys)
    
    # 2. Pacote de Rede (O Segredo: Mandar a Pub Key de quem envia!)
    network_packet = {
        "envelope": envelope,
        "signature": signature,
        "sender_sig_pub": alice.totem.get_public_keys()['sig']
    }
    
    # 3. Disparo
    url = f"http://127.0.0.1:{port}/receive"
    try:
        # Usamos json=network_packet para o requests manter o formato
        response = requests.post(url, json=network_packet)
        data = response.json()
        if response.status_code == 200:
            click.secho(f"✅ Sucesso: {data['status']}", fg='green', bold=True)
        else:
            click.secho(f"❌ Erro no Nó: {data['status']}", fg='red')
    except Exception as e:
        click.secho(f"❌ ERRO DE CONEXÃO: {e}", fg='red')

if __name__ == "__main__":
    cli()
