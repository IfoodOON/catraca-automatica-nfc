# Catraca Automatizada NFC — LAB 220

Sistema de controle de acesso veicular para a **LAB 220**, combinando um Arduino (sensor de proximidade + cancela com servo motor + relé/LED) com uma aplicação Python que faz a leitura de cartões NFC e exibe uma interface gráfica com o status em tempo real do sistema.

> Status: projeto em desenvolvimento inicial. A estrutura de pastas e o firmware do Arduino já estão prontos; a aplicação Python (interface, comunicação serial e leitura NFC) está sendo construída.

## Funcionamento

1. O sistema inicia e aguarda a chegada de um veículo.
2. O sensor de proximidade, ligado ao Arduino, detecta a aproximação e avisa a aplicação Python via Serial (`CARRO`).
3. A interface solicita a aproximação do cartão NFC.
4. O cartão é lido pelo leitor NFC USB conectado ao computador.
5. Se autorizado: a aplicação envia `ABRIR` ao Arduino, o servo abre a cancela e a interface informa acesso liberado.
6. Se não autorizado: a interface informa acesso negado e a cancela permanece fechada.
7. Após a passagem do veículo, o Arduino aguarda alguns segundos e fecha a cancela lentamente, avisando a aplicação (`FECHADA`).
8. O sistema volta ao estado inicial, aguardando o próximo veículo.

## Estrutura das pastas

```
arduino/
  catraca_producao/   # Firmware definitivo (sensor + servo + relé + protocolo Serial)
  catraca_teste/       # Sketch apenas para testar sensor/servo/LED isoladamente
src/
  config/              # Configurações do sistema (porta COM, parâmetros, etc.)
  core/                # Lógica principal / máquina de estados do fluxo de acesso
  hardware/            # Comunicação Serial (Arduino) e comunicação NFC (leitor USB)
  gui/                 # Interface gráfica (CustomTkinter) e seus componentes
  resources/           # Ícones e imagens usados pela interface
docs/                  # Fluxograma e demais documentos de referência do projeto
requirements.txt       # Dependências Python
```

## Dependências

- Python 3.11+
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — interface gráfica
- [pyserial](https://pyserial.readthedocs.io/) — comunicação com o Arduino
- [pyscard](https://pyscard.sourceforge.io/) — comunicação com o leitor NFC USB
- [Pillow](https://python-pillow.org/) — manipulação de imagens/ícones na interface
- [PyInstaller](https://pyinstaller.org/) — geração do executável Windows

Instale tudo com:

```bash
pip install -r requirements.txt
```

## Como executar

```bash
python src/main.py
```

## Como gerar o executável

```bash
pyinstaller --noconfirm --onefile --windowed --name CatracaLAB220 --add-data "src/resources;resources" src/main.py
```

O executável final ficará em `dist/CatracaLAB220.exe`.

## Como adicionar novas funcionalidades

O projeto foi estruturado para crescer sem exigir reescrita das partes existentes:

- **Banco de dados / histórico de acessos**: adicionar um módulo de persistência dentro de `src/core/`, consumido pela máquina de estados sem acoplar a interface diretamente ao banco.
- **Login de usuários**: novo módulo em `src/core/`, com uma tela adicional em `src/gui/`.
- **Múltiplos leitores NFC / câmera / reconhecimento facial**: novos módulos em `src/hardware/`, mantendo a mesma interface de eventos usada hoje pelo leitor NFC único.
- **Integração com APIs / rede / Wi-Fi / sistema web**: módulo dedicado que consome os mesmos eventos do `core`, sem alterar a lógica de acesso existente.

## Versionamento

O projeto usa Git desde o início, com commits seguindo o padrão:

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `refactor:` reorganização sem mudança de comportamento
- `docs:` atualização de documentação
- `style:` ajustes visuais/formatação
