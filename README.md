# SILED Estratégico

Sistema de acompanhamento de processos e contratos, reconstruído a partir do vídeo de referência de Felipe Freire Nunes. Mantém o tema azul-escuro, os cinco indicadores, o menu lateral, o quadro vertical por situação, o cadastro com anexos e os painéis de usuário e acessibilidade.

O projeto inclui as páginas que faltavam nos arquivos originais e usa um banco SQLite persistente. Não depende de chave de inteligência artificial.

**Para outra pessoa entrar pela internet, é necessário hospedar o sistema. Colocar os arquivos no GitHub permite compartilhar o código; isso, sozinho, não cria um endereço do SILED.** Veja o [guia de acesso pela internet](docs/HOSPEDAGEM.md).

## Começar no Windows

1. Instale o Python 3.10 ou superior pelo [site oficial](https://www.python.org/downloads/windows/), incluindo o Python Launcher (`py`).
2. Baixe o projeto e extraia o ZIP para uma pasta. Não execute os arquivos dentro do ZIP.
3. Abra `configurar_windows.bat` com dois cliques. Ele cria o ambiente Python, instala as dependências e solicita o cadastro do primeiro administrador.
4. Informe seu CPF, nome e uma senha de 12 a 128 caracteres. A senha não aparece enquanto você digita no terminal. Digite a mesma senha novamente para confirmar.
5. Quando a configuração terminar, abra `iniciar.bat`. O navegador será aberto em `http://127.0.0.1:5000`.
6. Entre usando o CPF e a senha cadastrados. Para o administrador, mantenha a opção **UNIDADE CENTRAL INTEGRADA - Acesso geral** no campo de órgão.

Mantenha a janela do servidor aberta enquanto usa o sistema. Para encerrar, pressione `Ctrl+C` nessa janela. Na próxima vez, basta abrir `iniciar.bat`; os dados continuam salvos.

O [guia de instalação](docs/INSTALACAO.md) explica o procedimento manual, problemas comuns e o uso no VS Code.

## O que está funcionando

- Entrada com usuário previamente cadastrado e senha protegida por hash.
- Dois perfis: administrador, com visão geral; fiscalizador, com acesso aos processos do próprio órgão.
- Cadastro e edição de processos, andamento, valores, prazos, riscos e situação.
- Cinco grupos no quadro: recebido, em análise, em acompanhamento, em alerta e concluído.
- Anexos privados, com download condicionado ao acesso ao processo.
- Exportação dos processos visíveis para CSV, compatível com Excel.
- Relatório mensal salvo no banco, com seleção do período e opção de impressão.
- Registro de entradas e saídas, painel do usuário, modos claro/escuro/contraste e tamanho de texto.
- Cadastro de usuários pelo administrador e solicitação de recuperação de senha.
- Espaço para incorporar um relatório Power BI quando uma URL autorizada for configurada.

O [guia de uso](docs/USO.md) apresenta um exemplo completo, do primeiro cadastro até o relatório.

## Limites desta versão

- A marca no cabeçalho foi aproximada com texto e CSS. O brasão e os arquivos oficiais de identidade visual não foram fornecidos. A tela é um protótipo e não comprova vínculo oficial com órgão público.
- Recuperação de senha registra uma solicitação para o administrador. Não envia e-mail nem gera link automático. A redefinição é feita pelo responsável no servidor.
- O relatório é uma síntese local dos processos cuja última atualização ocorreu no mês selecionado. Não substitui análise técnica, não consulta IA externa e não é uma fotografia completa de todas as alterações ocorridas no mês.
- Power BI depende de relatório, permissões e eventual licenciamento da sua organização. Não há um relatório real incluído.
- Anexos têm limite de dez arquivos e 25 MB por envio. O sistema restringe extensões, mas não contém serviço de análise antivírus.
- SQLite e armazenamento local atendem esta versão em uma única instância. Para várias instâncias ou maior volume de gravações simultâneas, será necessário migrar o banco e os anexos.
- Os arquivos `.bat`, PowerShell e VBS foram preparados para Windows. A execução local de desenvolvimento e dos testes foi feita em Linux; o fluxo de CI também está configurado para Windows.

## Estrutura do projeto

```text
siled/
  __init__.py        Criação do aplicativo e configuração
  db.py              Banco de dados e usuários
  services.py        Validação, indicadores e relatório
  views.py           Rotas e operações do sistema
  templates/         Telas HTML
  static/            CSS, JavaScript e ícone
tests/               Testes de funcionamento e acesso
docs/                Instalação, uso, hospedagem e validação
main.py              Servidor Waitress
manage.py            Administração pelo terminal
render.yaml          Exemplo de hospedagem com disco persistente
Dockerfile           Alternativa de execução em contêiner
```

O diretório `instance/` é criado no primeiro uso e guarda banco, anexos e chave local. Ele está excluído do Git. Não envie esse diretório, o `.env`, senhas ou dados reais de usuários ao repositório.

## Instalação manual

Exemplo para Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py create-user --role administrador
python main.py --open-browser
```

Para criar outro fiscalizador pelo terminal:

```bash
python manage.py create-user --role fiscalizador --orgao SESAU
```

O administrador também encontra o cadastro na tela **Usuário → Gerenciar usuários**.

## Testes

Com o ambiente Python ativado:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes usam usuários fictícios e banco temporário. Cobrem entrada, bloqueio por órgão, cadastro e edição, persistência, anexos, relatório, CSV, sessões e validações. Veja as evidências e os limites em [VALIDACAO.md](docs/VALIDACAO.md).

## Créditos e uso

Projeto de referência: Felipe Freire Nunes. Não foi adicionada licença de redistribuição automaticamente; o titular pode escolher uma licença antes de autorizar outros usos.
