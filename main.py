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
    """Envia mensagem apenas após validação gestual no Totem."""
    alice = get_agent(sender_id)
    bob = get_agent(receiver_id)
    
    click.secho(f"\n--- 💍 AGUARDANDO TOTEM ({sender_id}) ---", fg='yellow', bold=True)
    click.echo("Sensores ativos. Realize sua sequência gestual:")
    click.echo("0:Polegar | 1:Indicador | 2:Médio | 3:Anelar")
    
    # Simula a captura dos sensores do SmartRing
    gesture_input = click.prompt("Digite a sequência (ex: 120)", type=str)
    gesture_list = [int(d) for d in gesture_input]

    # O Agente pede permissão ao Totem
    if not alice.totem.verify_gesture(gesture_list):
        click.secho("❌ ERRO: Gesto incorreto! O Totem permaneceu trancado.", fg='red', bold=True)
        return

    click.secho("✅ GESTO RECONHECIDO. Assinando com Ed25519...", fg='green')
    
    sim = DSANSimulator([alice, bob])
    payload = {"type": "DREX_TRANSF", "content": msg}
    
    if sim.send_message(sender_id, receiver_id, payload):
        click.secho("🚀 Transação enviada com sucesso!", fg='cyan')

@cli.command()
@click.argument('name')
def audit(name):
    """Inspeciona o Ledger imutável de um agente."""
    agent = get_agent(name)
    
    click.secho(f"\n📊 RELATÓRIO DE AUDITORIA: {name.upper()}", fg='yellow', bold=True)
    click.echo(f"ID Soberano: {agent.id}")
    click.echo(f"State Hash:  ", nl=False)
    
    # CORREÇÃO: Removido o .hex() porque o state_hash agora já é uma string
    click.secho(agent.state_hash, fg='magenta') 
    
    click.echo(f"Log Height:  {len(agent.local_log)} eventos")
    click.echo("-" * 40)
    
    for i, entry in enumerate(agent.local_log):
        ev = entry['event']
        click.echo(f"[{i}] ", nl=False)
        click.secho(f"{ev['type']}", fg='green', nl=False)
        
        # Extrai o conteúdo para exibição
        content = ev.get('data', {}).get('content', 'N/A')
        
        # Se for um dicionário (nosso payload json decifrado), converte pra string pra ler
        if isinstance(content, dict):
            content = str(content)
            
        click.echo(f" | Data: {content[:50]}...")

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