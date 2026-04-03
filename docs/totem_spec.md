# Especificação Técnica: Totem Criptográfico (v1.1)

O Totem é a **Raiz de Confiança (Root of Trust)** da DSAN. Sua função é isolar as chaves privadas do ambiente de execução do Agente (que pode estar na nuvem ou em hardware menos seguro).

## 1. Arquitetura de Isolamento
No simulador v1.1, a classe `DSANTotem` simula um elemento seguro (Secure Element):
- **Geração de Chaves:** Utiliza a curva elíptica `Ed25519`.
- **Interface de Assinatura:** O Agente envia um `payload` e recebe uma `assinatura`. A chave privada nunca deixa o escopo da classe `Totem`.

## 2. Protocolo de Envelope
Cada mensagem gerada pelo Totem segue o formato:
- **Payload:** Os dados da aplicação.
- **Nonce:** Timestamp de alta precisão para evitar ataques de Replay.
- **Sender_ID:** Identificador soberano do remetente.

## 3. Requisitos de Hardware (Futuro)
Para a implementação física, os alvos são:
- **ESP32-S3:** Utilizando o Secure Boot e Flash Encryption.
- **Raspberry Pi CM4:** Utilizando módulos TPM externos.
- **Android (OffCloud):** Utilizando o Android Keystore System / StrongBox.

## 4. Vetores de Ataque Mitigados
- **Extração de Chaves:** Como a chave reside no Totem, um Agente comprometido não pode roubar a identidade do usuário.
- **Manipulação de Histórico:** O Totem assina o estado atual, permitindo que qualquer nó da rede verifique a integridade do log.
## Validação de Fluxo v1.1
O protocolo foi testado com sucesso em ambiente distribuído (Codespaces) apresentando:
1. **Handshake Bi-direcional:** Alice e Bob trocam estados e atualizam hashes locais.
2. **Persistência JSON:** O estado sobrevive ao encerramento do processo.
3. **Imutabilidade Reversa:** O `prev_hash` de cada evento impede a reescrita do histórico sem quebra do `state_hash` final.