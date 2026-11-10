# Verificação da reconstrução

## Resultado

O projeto foi reconstruído com as telas HTML ausentes nos arquivos originais, persistência em SQLite e acesso por usuários cadastrados. A suíte automatizada terminou com **28 testes aprovados**, em Python 3.12.14/Linux. O servidor Waitress também passou por **oito cenários de aceitação HTTP**, com dados fictícios e diretório temporário.

Isso registra os comportamentos verificados nesta versão. Não representa implantação em produção, execução em Windows nem teste de carga.

## Funcionamento e acesso

| Área | Verificação realizada |
| --- | --- |
| Páginas | Entrada, recuperação, quadro, formulário, relatório, Power BI e administração renderizaram sem erro. |
| Autenticação | Usuário inexistente, senha incorreta e órgão incompatível foram recusados. |
| Limite de tentativas | O bloqueio foi aplicado após cinco falhas no período de quinze minutos. |
| Formulários | Pedidos sem token de sessão válido foram recusados; dados inválidos não foram gravados. |
| Processos | Cadastro, edição, valores em centavos, código único, situação em análise e preservação após nova inicialização foram conferidos. |
| Edição simultânea | Uma versão antiga do formulário não sobrescreveu uma atualização já salva. |
| Órgãos | Fiscalizador não consultou, alterou ou baixou anexos de outro órgão nem abriu a administração. |
| Anexos | Nomes iguais geraram arquivos internos diferentes; downloads preservaram o conteúdo; falhas no envio desfizeram o cadastro incompleto. |
| CSV | Exportação respeitou o perfil e protegeu células que poderiam ser interpretadas como fórmulas. |
| Relatórios | Filtro mensal, horário de Porto Velho e gravação da síntese no banco foram conferidos. |
| Senha e sessão | Alteração da versão de autenticação invalidou sessões anteriores. |
| Power BI | Endereços fora dos domínios HTTPS permitidos não geraram iframe. Um endereço fictício permitido validou a renderização, sem acessar relatório real. |
| Cabeçalhos | Políticas de conteúdo e opções básicas de proteção de respostas foram conferidas. |

## Aceitação com o servidor em execução

O teste HTTP usou `main.py` com Waitress, em endereço de loopback e porta temporária. Foram confirmados:

1. Redirecionamento de pessoa sem sessão para a entrada.
2. Criação inicial do administrador por variáveis de ambiente e entrada com credenciais fictícias.
3. Resposta HTTP 200 nas cinco páginas internas e nos arquivos CSS e JavaScript.
4. Cadastro com anexo e download com comparação do conteúdo byte a byte.
5. Exportação CSV contendo o processo recém-cadastrado.
6. Geração e reabertura do relatório mensal.
7. Preservação de usuário, processo, anexo e relatório após encerrar o processo servidor e iniciar outro.
8. Encerramento da sessão por saída e bloqueio de nova consulta autenticada.

Os arquivos originais enviados pelo usuário foram preservados. As dependências instaladas passaram por `pip check`, e o JavaScript passou pela verificação de sintaxe do Node.

## Conferência visual

Foram comparadas com o vídeo as telas de entrada, quadro, cadastro, relatório e Power BI. O tema escuro, os indicadores, a barra lateral, os blocos verticais e os painéis superiores foram mantidos. As margens e os espaços do quadro foram ajustados após a comparação.

Os painéis de usuário e acessibilidade e a troca para o tema claro foram inspecionados no navegador. Entrada, quadro e cadastro também foram renderizados em quadros de 390 pixels para conferir a adaptação a telas estreitas.

A prévia gerenciada disponível não executou o ambiente Python do projeto. Por isso, a inspeção visual utilizou HTML gerado pelo próprio Flask com dados fictícios, CSS e JavaScript reais. O envio dos formulários foi validado pelos testes e pelo servidor HTTP descritos acima; não foi feito um fluxo completo de preenchimento e gravação pelo navegador dessa prévia.

## O que ainda depende do ambiente de destino

- Executar os atalhos e a instalação em um computador Windows. A configuração de GitHub Actions contempla Windows e Linux, com Python 3.10 e 3.12; um workflow incluído no código não comprova que já houve execução remota.
- Implantar em uma hospedagem com HTTPS e armazenamento persistente e testar o endereço externo.
- Configurar um relatório Power BI verdadeiro e conferir as permissões dos usuários.
- Validar impressão com a impressora ou o destino PDF usado pela organização.
- Definir backup, restauração, administração de usuários e rotina de atendimento às solicitações de senha.

O projeto não contém banco preenchido, senhas de acesso, `.env` real, vídeo de referência ou documentos privados.
