import requests
import click
from dsan_sim.agent import DSANAgent

@click.group()
def cli():
    """🛡️ DSAN Sovereign Console - v1.5"""
    pass

@cli.command()
@click.argument('sender_id')
@click.argument('receiver_id')
@click.argument('msg')
@click.option('--port', default=5001, help="Porta de rede")
def send(sender_id, receiver_id, msg, port):
    """Teletransporta mensagem via rede real."""
    # Instanciar recarrega do disco automaticamente graças à correção no agent.py
    alice = DSANAgent(sender_id)
    bob = DSANAgent(receiver_id) 
    
    click.secho(f"\n--- 💍 AGUARDANDO TOTEM ({sender_id.upper()}) ---", fg='yellow', bold=True)
    gesture_input = click.prompt("Digite a sequência gestual", type=str)
    gesture_list = [int(d) for d in gesture_input]

    if not alice.totem.verify_gesture(gesture_list):
        click.secho("❌ ERRO: Gesto incorreto!", fg='red', bold=True)
        return

    payload = {"type": "DREX_TRANSF", "content": msg}
    receiver_keys = bob.totem.get_public_keys()
    signature, envelope = alice.sign_message(payload, recipient_pub_keys=receiver_keys)
    
    network_packet = {
    "envelope": envelope,
    "signature": signature[:-1] + "f", # Troca o último caractere por 'f'
    "sender_sig_pub": alice.totem.get_public_keys()['sig']
}
    
    url = f"http://127.0.0.1:{port}/receive"
    try:
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