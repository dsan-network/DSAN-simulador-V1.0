# Modelagem de Ameaças (STRIDE) - v1.1

Este documento descreve as mitigações implementadas no simulador DSAN contra vetores de ataque comuns em redes descentralizadas.

## 1. Spoofing (Falsificação de Identidade)
- **Ameaça:** Um nó malicioso forja o cabeçalho `sender_id` para se passar por outro usuário.
- **Mitigação [VALIDADA]:** O envelope completo (dados + cabeçalho) é assinado pelo Totem usando a curva **Ed25519**. Se o ID do remetente for alterado após a assinatura, a verificação da Chave Pública falha.

## 2. Tampering (Adulteração de Dados)
- **Ameaça:** Alteração manual do banco de dados local ou injeção de pacotes na rede.
- **Mitigação [VALIDADA]:** O histórico utiliza **Hash-Chaining (SHA-256)**. Cada novo evento carrega o hash do evento anterior (`prev_hash`). Qualquer alteração quebra a corrente, sendo imediatamente detectada na auditoria do `state_hash`.

## 3. Repudiation (Repúdio)
- **Ameaça:** Um agente nega ter enviado uma mensagem.
- **Mitigação:** A chave privada é isolada na classe `DSANTotem`. Como o agente de IA não tem acesso à chave, todas as assinaturas válidas são garantidamente originadas pela intenção do portador do Totem físico.

## 4. Information Disclosure (Exposição de Informação)
- **Ameaça:** Vazamento de dados em trânsito.
- **Status:** Em aberto. O simulador v1.1 garante integridade e autenticidade, mas os payloads ainda estão em texto claro. Criptografia ponta a ponta (E2EE) está planejada para a v1.2.

## 5. Denial of Service (Negação de Serviço)
- **Ameaça:** Inundação de mensagens repetidas.
- **Mitigação [VALIDADA]:** O sistema de envelope exige um `nonce` (timestamp). O agente armazena o último nonce validado por remetente. Mensagens antigas ou repetidas (*Replay Attacks*) são dropadas em O(1).