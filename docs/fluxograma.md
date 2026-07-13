# Fluxograma — Catraca Automatizada NFC (LAB 220)

Fluxo de funcionamento fornecido pelo usuário em 2026-07-13, correspondente 1:1 à lógica já implementada em `arduino/catraca_producao/catraca_producao.ino`.

```
                    ┌───────────────────────┐
                    │    INICIAR SISTEMA    │
                    └──────────┬────────────┘
                               │
                               ▼
                ┌───────────────────────────┐
                │ Servo em 175° (Fechada)   │
                │ LED Desligado             │
                └──────────┬────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │ Monitorar Sensor de Carro   │
              └──────────┬──────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
     NÃO DETECTOU                  DETECTOU
          │                             │
          │                             ▼
          │               ┌─────────────────────────┐
          │               │ Enviar "CARRO" ao PC    │
          │               │ Acender LED             │
          │               └──────────┬──────────────┘
          │                          │
          │                          ▼
          │             ┌────────────────────────────┐
          │             │ Interface solicita NFC     │
          │             │ Aguardar comando ABRIR     │
          │             └──────────┬─────────────────┘
          │                        │
          │          ┌─────────────┴─────────────┐
          │          │                           │
          │      NFC NEGADO                 NFC AUTORIZADO
          │          │                           │
          │          ▼                           ▼
          │  Continuar aguardando      Receber comando "ABRIR"
          │      novo cartão                    │
          │                                     ▼
          │                     ┌──────────────────────────┐
          │                     │ Abrir Servo para 90°     │
          │                     │ Enviar "ABERTA" ao PC    │
          │                     │ LED permanece ligado     │
          │                     └──────────┬───────────────┘
          │                                │
          │                                ▼
          │                  ┌───────────────────────────┐
          │                  │ Aguardar saída do veículo │
          │                  └──────────┬────────────────┘
          │                             │
          │                  Carro ainda presente?
          │                             │
          │               ┌─────────────┴────────────┐
          │               │                          │
          │              SIM                        NÃO
          │               │                          │
          │               │                          ▼
          │               │            ┌────────────────────────┐
          │               │            │ Enviar "SEM_CARRO" PC  │
          │               │            │ Esperar 3 segundos     │
          │               │            └──────────┬─────────────┘
          │               │                       │
          │               └───────────────────────┘
          │                                       ▼
          │                      ┌──────────────────────────┐
          │                      │ Fechar lentamente Servo  │
          │                      │ até 175°                 │
          │                      └──────────┬───────────────┘
          │                                 │
          │                                 ▼
          │                     ┌──────────────────────────┐
          │                     │ Enviar "FECHADA" ao PC   │
          │                     │ Apagar LED               │
          │                     └──────────┬───────────────┘
          │                                 │
          └─────────────────────────────────┘
                                            │
                                            ▼
                             Retornar ao monitoramento
```

## Estados relevantes para o lado Python (`src/core`)

| Estado              | Gatilho                                   | Origem            |
|----------------------|--------------------------------------------|-------------------|
| `IDLE`               | Sistema iniciado / `FECHADA` recebida      | Arduino           |
| `AGUARDANDO_CARTAO`   | `CARRO` recebido do Arduino                | Arduino           |
| `VALIDANDO_CARTAO`    | Cartão lido pelo leitor NFC (USB, pyscard) | Python            |
| `ACESSO_NEGADO`       | Cartão não autorizado                      | Python (volta para `AGUARDANDO_CARTAO`) |
| `ACESSO_LIBERADO`     | Cartão autorizado → envia `ABRIR`          | Python → Arduino  |
| `ABERTA`              | `ABERTA` recebido do Arduino                | Arduino           |
| `AGUARDANDO_SAIDA`    | Implícito enquanto o Arduino aguarda o carro sair | Arduino (interno) |
| `FECHANDO`            | `SEM_CARRO` recebido, Arduino inicia fechamento | Arduino       |
| `FECHADA`             | `FECHADA` recebido → volta a `IDLE`        | Arduino           |

A decisão de autorizar/negar o cartão acontece inteiramente no PC (o Arduino não sabe nada sobre NFC) — por isso `NFC NEGADO` nunca chega a virar uma mensagem Serial; ele só mantém o Arduino esperando, sem nunca receber `ABRIR`.
