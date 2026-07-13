# Catraca Automatizada NFC — LAB 220

Sistema de controle de acesso veicular para a **LAB 220**, combinando um Arduino (sensor de proximidade + cancela com servo motor + relé/LED) com uma aplicação Python que faz a leitura de cartões NFC e exibe uma interface gráfica com o status em tempo real do sistema.

> Status: funcional e testado com hardware real (Arduino + leitor NFC USB). Inclui tela de administração para cadastro de cartões e geração de executável standalone para Windows.

## Funcionamento

1. O sistema inicia e aguarda a chegada de um veículo.
2. O sensor de proximidade, ligado ao Arduino, detecta a aproximação e avisa a aplicação Python via Serial (`CARRO`).
3. A interface solicita a aproximação do cartão NFC.
4. O cartão é lido pelo leitor NFC USB conectado ao computador.
5. Se autorizado: a aplicação envia `ABRIR` ao Arduino, o servo abre a cancela e a interface informa acesso liberado.
6. Se não autorizado: a interface informa acesso negado e a cancela permanece fechada.
7. Após a passagem do veículo, o Arduino aguarda alguns segundos e fecha a cancela lentamente, avisando a aplicação (`FECHADA`).
8. O sistema volta ao estado inicial, aguardando o próximo veículo.

### Cadastro de funcionários/cartões

Clicando 6 vezes seguidas (em até 2s) no nome "LAB 220" no cabeçalho da interface, é pedida uma senha (ver/alterar em `src/config/admin.json`) que abre a tela de administração: lista os cartões já cadastrados, permite remover, e permite cadastrar um novo aproximando o cartão do leitor (sem que isso conte como uma tentativa normal de acesso).

## Estrutura das pastas

```
arduino/
  catraca_producao/   # Firmware definitivo (sensor + servo + relé + protocolo Serial)
  catraca_teste/       # Sketch apenas para testar sensor/servo/LED isoladamente
src/
  config/              # Configurações do sistema (porta COM, parâmetros, etc.)
  core/                # Lógica principal / máquina de estados do fluxo de acesso
  hardware/            # Comunicação Serial (Arduino) e comunicação NFC (leitor USB)
  gui/                 # Interface gráfica (CustomTkinter), incluindo gui/admin.py (tela de cadastro)
  resources/           # Ícones e imagens usados pela interface
docs/                  # Fluxograma e demais documentos de referência do projeto
executar.bat            # Atalho: abre o app com duplo clique (usa o .venv já instalado)
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
pyinstaller --noconfirm --onefile --windowed --name CatracaLAB220 src/main.py
```

O executável final ficará em `dist/CatracaLAB220.exe`. Ele pode ser copiado e executado em qualquer lugar (ex: Área de Trabalho) — na primeira execução, cria `cartoes.json` e `admin.json` na mesma pasta onde o `.exe` está, e registra logs em `catraca.log` ali também.

Se `src/resources/` (ícones/imagens) ganhar arquivos no futuro, adicione `--add-data "src/resources;resources"` ao comando pra empacotá-los junto.

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
