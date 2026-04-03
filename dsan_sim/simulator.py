class DSANSimulator:
    def __init__(self, agents, network_loss=0):
        self.agents = {a.id: a for a in agents}
        self.network_loss = network_loss

    def send_message(self, sender_id, receiver_id, payload):
        sender = self.agents.get(sender_id)
        receiver = self.agents.get(receiver_id)
        
        if not sender or not receiver:
            return False

        # Na v1.2, buscamos o dicionário de chaves do destinatário para cifrar
        receiver_keys = receiver.totem.get_public_keys()
        
        # Alice assina e cifra a mensagem usando as chaves do Bob
        signature, envelope = sender.sign_message(payload, recipient_pub_keys=receiver_keys)
        
        # O Simulador entrega para o Bob (passando a chave de ASSINATURA da Alice)
        sender_sig_pub = sender.totem.get_public_keys()['sig']
        success = receiver.receive(envelope, signature, sender_sig_pub)
        
        return success