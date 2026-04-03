import click
from dsan_sim import DSANAgent, DSANSimulator

session_agents = {}

def get_agent(name):
    """Auxiliar para carregar agente da memória ou do disco."""
    if name not in session_agents:
        session_agents[name] = DSANAgent(name)
    return session_agents[name]

@click.group()
def cli():
    """🛡️ DSAN Sovereign Console - v1.1"""
    pass

@cli.command()
@click.argument('sender_id')
@click.argument('receiver_id')
@click.argument('msg')
def send(sender_id, receiver_id, msg):
    """Envia uma mensagem assinada entre agentes."""
    alice = get_agent(sender_id)
    bob = get_agent(receiver_id)
    
    sim = DSANSimulator([alice, bob], network_loss=0)
    
    click.secho(f"🚀 Enviando de {sender_id}...", fg='cyan')
    sim.send_message(sender_id, receiver_id, {"type": "CHAT", "content": msg})
    click.secho("✅ Protocolo de entrega finalizado.", fg='green')

@cli.command()
@click.argument('name')
def audit(name):
    """Inspeciona o Ledger imutável de um agente."""
    agent = get_agent(name)
    
    click.secho(f"\n📊 RELATÓRIO DE AUDITORIA: {name.upper()}", fg='yellow', bold=True)
    click.echo(f"ID Soberano: {agent.id}")
    click.echo(f"State Hash:  ", nl=False)
    click.secho(agent.state_hash.hex(), fg='magenta')
    click.echo(f"Log Height:  {len(agent.local_log)} eventos")
    click.echo("-" * 40)
    
    for i, entry in enumerate(agent.local_log):
        ev = entry['event']
        click.echo(f"[{i}] ", nl=False)
        click.secho(f"{ev['type']}", fg='green', nl=False)
        click.echo(f" | Data: {ev['data']['payload'].get('content', 'N/A')[:20]}...")

@cli.command()
@click.argument('target')
@click.argument('fake_sender')
def attack(target, fake_sender):
    """Simula um ataque de Spoofing contra um agente."""
    victim = get_agent(target)
    hacker = DSANAgent("hacker_temp")
    
    click.secho(f"💀 INICIANDO ATAQUE DE SPOOFING CONTRA {target.upper()}...", fg='red', bold=True)
    
    # Hacker assina, mas mente sobre quem enviou
    payload = {"type": "HACK", "content": "TRANSFERIR_TUDO_PARA_MIM"}
    sig, envelope = hacker.sign_message(payload)
    envelope["sender_id"] = fake_sender # O "Tampering"
    
    click.echo(f"[*] Hacker enviando mensagem como se fosse '{fake_sender}'...")
    
    # Tentativa de entrega (Usando a chave da vítima real como base de comparação)
    # Nota: Em uma rede real, o Bob buscaria a chave de 'fake_sender' num diretório
    real_sender = get_agent(fake_sender)
    success = victim.receive(envelope, sig, real_sender.public_key_bytes)
    
    if not success:
        click.secho(f"🛡️ DEFESA ATIVA: {target} rejeitou a mensagem fraudulenta!", fg='green', bold=True)
    else:
        click.secho(f"❌ VULNERABILIDADE: O ataque funcionou!", bg='red', fg='white')

if __name__ == "__main__":
    cli()