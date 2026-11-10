# Como permitir acesso de outro lugar

## O que muda

No seu computador, `http://127.0.0.1:5000` abre o SILED local. Na casa ou no trabalho de outra pessoa, esse endereço aponta para o computador dela, não para o seu.

Para compartilhar o mesmo sistema e os mesmos dados, execute uma instalação em um servidor com endereço HTTPS. As pessoas acessam esse endereço e entram com usuários cadastrados. Um repositório GitHub, inclusive público, compartilha o código e não substitui esse servidor. GitHub Pages não executa este aplicativo Python com banco e anexos.

## Opção preparada: Render

O arquivo `render.yaml` descreve uma instalação com um serviço Python e um disco persistente. **O serviço e o disco indicados podem ter cobrança. Confira o plano e o valor na plataforma antes de confirmar a criação.** Este arquivo é uma configuração de exemplo; não significa que um serviço já foi contratado ou publicado.

### 1. Colocar o projeto no GitHub

Crie um repositório, preferencialmente privado enquanto valida o sistema. Envie o conteúdo desta pasta, preservando `siled/`, `docs/`, `tests/` e os arquivos de configuração. Não envie a pasta `instance/`, o `.env`, ambientes virtuais, senhas, bancos ou documentos reais.

### 2. Conectar o Render ao repositório

Entre no [Render](https://dashboard.render.com/), conecte o repositório e use a opção de criar um serviço por **Blueprint**, apontando para `render.yaml`. Se a interface mudar, procure a implantação a partir de um repositório e arquivo Blueprint.

Revise a configuração proposta antes de confirmar. O exemplo usa uma única instância e um disco em `/var/data`, porque SQLite e os anexos precisam permanecer disponíveis após reinícios e novas publicações.

### 3. Configurar o primeiro administrador

Preencha os segredos solicitados pela plataforma:

| Variável | Valor a informar |
| --- | --- |
| `SILED_ADMIN_CPF` | Identificador de onze dígitos do primeiro administrador. |
| `SILED_ADMIN_NAME` | Nome a mostrar no painel. |
| `SILED_ADMIN_PASSWORD` | Senha exclusiva, de 12 a 128 caracteres. |

O Blueprint também define:

| Variável | Finalidade |
| --- | --- |
| `SILED_ENV=production` | Exige chave de sessão e cookies seguros para HTTPS. |
| `SILED_DATA_DIR=/var/data` | Banco e anexos no disco persistente. |
| `FLASK_SECRET_KEY` | Chave aleatória gerada pela plataforma. |
| `TRUST_PROXY=1` | Usa o proxy reverso da hospedagem para protocolo e IP. |

As variáveis de primeiro administrador só criam a conta se o banco ainda estiver vazio. Alterá-las depois não redefine uma senha existente. Após confirmar o primeiro acesso, remova `SILED_ADMIN_PASSWORD` dos segredos da hospedagem; para redefinir a senha, use `manage.py reset-password` no servidor. Mantenha a chave de sessão estável e protegida.

### 4. Publicar e testar

Após conferir os custos e confirmar a implantação na plataforma:

1. Aguarde a conclusão do build e do início do serviço.
2. Abra o endereço HTTPS que a plataforma informar.
3. Entre com o administrador configurado.
4. Cadastre um processo e um anexo de teste.
5. Reinicie o serviço pela plataforma e confirme que o processo e o anexo continuam disponíveis.
6. Cadastre um fiscalizador e confira, em outra sessão, que ele só acessa o próprio órgão.
7. Compartilhe o endereço HTTPS e as credenciais de cada usuário por um canal privado.

Se o build for configurado manualmente, os comandos são:

```text
Build: pip install -r requirements.txt
Start: python main.py --host 0.0.0.0
Health check: /healthz
```

Configure a mesma pasta de disco e as mesmas variáveis. Uma hospedagem com armazenamento temporário pode perder o banco e os anexos ao reiniciar ou publicar uma versão.

## Outra hospedagem ou servidor da organização

É possível usar um servidor Python ou o `Dockerfile` incluído. Configure HTTPS no proxy reverso, uma chave de sessão aleatória com pelo menos 32 caracteres e uma pasta persistente com permissão de escrita para o usuário do aplicativo.

No exemplo Docker, o usuário do processo tem UID 10001 e a pasta de dados é `/var/data`. Monte um volume persistente nesse caminho. O contêiner não configura certificado, domínio nem HTTPS por conta própria. Use `TRUST_PROXY=1` somente se o acesso ao aplicativo passar exclusivamente pelo proxy confiável configurado para ele.

Não publique o servidor local de desenvolvimento diretamente na internet. `main.py` já usa Waitress, mas a hospedagem ainda precisa cuidar de HTTPS, persistência e backups. Use uma única instância com o banco SQLite desta versão.

## Antes do uso com dados reais

Defina quem administra usuários, quem pode acessar cada órgão, quem mantém backups e como solicitações de senha serão atendidas. A conta SILED não tem vínculo automático com cadastros oficiais, SIGEF ou Microsoft.

Faça backup consistente da pasta de dados com o serviço parado, teste a restauração e restrinja o acesso à cópia. A escolha de uma infraestrutura para operação institucional deve ser validada pela equipe responsável da organização.

## Referências

- [Flask: uso com Waitress](https://flask.palletsprojects.com/en/stable/deploying/waitress/)
- [Render: implantação de Flask](https://render.com/docs/deploy-flask)
- [Render: discos persistentes](https://render.com/docs/disks)
