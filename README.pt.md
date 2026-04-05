🛡️ DSAN Simulator V1.6: Protocolo de ResiliênciaO DSAN (Decentralized Sovereign Agent Network) é um simulador de rede descentralizada de alta segurança. Ele utiliza um modelo de Totem Criptográfico para garantir que a identidade e a integridade dos dados sejam imutáveis, mesmo em ambientes de rede hostis.Esta versão (v1.6) foi testada contra ataques de Man-in-the-Middle (MitM) e falsificação de assinatura, provando-se matematicamente segura.

💎 Diferenciais do ProtocoloIdentidade Determinística: Chaves $Ed25519$ persistentes que garantem a "mente" do agente entre sessões.
1. Serialização Blindada (Vacuum JSON): Elimina falhas de validação causadas por formatação de caracteres ou espaços em branco.
2. Cifragem Híbrida: Troca de chaves $X25519$ com derivação de segredo via $HKDF$ para um canal $E2EE$ (End-to-End Encryption).
3. Defesa Ativa: O sistema invalida e descarta automaticamente qualquer pacote que sofra alteração de um único bit.

🛠️ Guia de Operação
1. Preparação do TerrenoCertifique-se de limpar identidades órfãs antes de iniciar uma nova rede de confiança:Bashrm -rf data/agents/*.json
2. Inicialização do Nó Soberano (Bob)No Terminal 1, inicie o receptor:Bashpython node.py bob 5001
3. O Despertar da Alice e o EnvioNo Terminal 2, gere as identidades e realize o teletransporte:Sincronização Inicial:Bashpython -c "from dsan_sim.agent import DSANAgent; DSANAgent('alice'); DSANAgent('bob')"
Envio Autorizado pelo Totem:Bashpython main.py send alice bob "Mensagem Criptografada V1.6" --port 5001

🔬 Anatomia da Segurança (O que validamos)O DSAN Simulator protege a informação em três camadas concêntricas:
-Camada Física (Gesto): A chave privada só é liberada após a sequência gestual 120.
-Camada de Integridade (Assinatura): O envelope é assinado digitalmente. Se o conteúdo for alterado, a assinatura quebra.
-Camada de Privacidade (Cifragem): O conteúdo viaja como ruído aleatório para qualquer um que não seja o destinatário original.

🚨 Relatório de Teste de Estresse (Ataque MitM)Durante o desenvolvimento da V1.6, simulamos um ataque alterando a assinatura no main.py.Resultado: O nó receptor identificou a discrepância e disparou um [ERRO INTERNO DE CRIPTOGRAFIA].Status: Aprovado. O sistema prefere o silêncio à aceitação de um dado corrompido.

Status: OPERATIONAL
Segurança: MIL-SPEC
Desenvolvedor: @subverso
