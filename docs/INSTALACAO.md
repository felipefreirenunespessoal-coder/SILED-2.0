# Instalação e manutenção local

## Windows, passo a passo

### 1. Preparar a pasta

Instale Python 3.10 ou superior com o Python Launcher. No GitHub, use **Code → Download ZIP**, extraia o arquivo e abra a pasta que contém `main.py` e `configurar_windows.bat`.

### 2. Configurar uma vez

Abra `configurar_windows.bat`. A primeira execução precisa de internet para baixar as dependências. Ao solicitar o primeiro usuário, preencha:

- CPF: os onze dígitos do identificador do usuário.
- Nome: o nome que aparecerá no painel.
- Senha: de 12 a 128 caracteres, repetida para confirmação. Não há uma senha padrão.

O aplicativo exige onze dígitos para o CPF; não valida os dígitos verificadores. O administrador deve conferir o cadastro antes de autorizar o acesso.

Se preferir PowerShell, execute `./configurar_windows.ps1` em um terminal que permita scripts locais. O arquivo `.bat` realiza a configuração sem depender da política de execução do PowerShell.

### 3. Abrir o SILED

Abra `iniciar.bat`. O endereço local é `http://127.0.0.1:5000`. A janela do servidor precisa permanecer aberta. Para parar, use `Ctrl+C`.

`abrir_siled_windows.vbs` é um atalho para iniciar o mesmo procedimento. `abrir_no_vscode.bat` abre a pasta no VS Code, se o comando `code` estiver instalado.

## Procedimento manual no Windows

Abra o Prompt de Comando dentro da pasta do projeto:

```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
.venv\Scripts\python.exe manage.py create-user --role administrador
.venv\Scripts\python.exe main.py --open-browser
```

Copie o `.env.example` somente na primeira instalação, para não substituir configurações existentes.

## VS Code

Abra `SILED.code-workspace`. Instale as extensões Python e Python Debugger sugeridas. No Windows, selecione `.venv\Scripts\python.exe` como interpretador. Em Linux/macOS, selecione `.venv/bin/python`.

O comando `F5` executa `main.py`. A instalação das dependências e o cadastro inicial devem ser feitos antes.

## Redefinir uma senha

Na pasta do projeto, execute o comando correspondente ao seu sistema:

```bat
.venv\Scripts\python.exe manage.py reset-password
```

Em Linux/macOS, com o ambiente ativado:

```bash
python manage.py reset-password
```

O terminal solicita CPF, nova senha e confirmação. A senha não é passada em argumento nem exibida. A redefinição invalida as sessões anteriores desse usuário. Confirme a identidade da pessoa por um canal conhecido antes de redefinir sua senha; a solicitação no formulário, isoladamente, não comprova identidade.

## Conferir o banco

```bash
python manage.py status
```

O comando informa quantos usuários, processos, anexos e relatórios estão armazenados, sem mostrar senhas.

## Backup e restauração

1. Pare o servidor e evite qualquer alteração durante a cópia.
2. Copie a pasta de dados inteira. Por padrão é `instance/`; se `SILED_DATA_DIR` estiver configurada, use esse diretório.
3. Guarde a cópia em local restrito. Ela contém dados de usuários, documentos e, no modo local, a chave de sessão.
4. Para restaurar, mantenha o servidor parado e recoloque a pasta no caminho configurado. Use a mesma versão do aplicativo e as mesmas configurações necessárias.
5. Inicie o servidor e confira a entrada, a quantidade de processos e a abertura de um anexo.

Não use GitHub como backup do banco ou dos anexos. Atualizar o código não deve substituir nem apagar a pasta de dados.

## Problemas comuns

| Mensagem ou situação | Como resolver |
| --- | --- |
| `py` não é reconhecido | Instale o Python Launcher pela instalação oficial do Python ou use o caminho do seu `python.exe` no procedimento manual. |
| Não foi possível instalar dependências | Confira a internet e a mensagem do terminal. Em rede corporativa, peça à TI a liberação necessária para o registro de pacotes. |
| CPF ou senha recusados | Use um usuário cadastrado; confira o órgão selecionado. Fiscalizadores devem escolher o órgão ao qual foram vinculados. |
| Muitas tentativas de entrada | Aguarde quinze minutos antes de tentar novamente. |
| A página local não abre | Confira se a janela do servidor está aberta e se você está no mesmo computador. |
| Porta 5000 ocupada | Execute `python main.py --port 5001 --open-browser` no ambiente ativado. |
| Formulário expirou | Recarregue a página e faça a entrada novamente, se necessário. |
| Anexo recusado | Confira extensão, quantidade e tamanho total do envio. |
| Outro usuário atualizou o processo | Reabra o processo, confira a alteração já salva e depois registre sua atualização. |
| Outra pessoa, em outro local, não abre o endereço | `127.0.0.1` aponta para o próprio computador de quem acessa. Siga o guia de hospedagem. |
