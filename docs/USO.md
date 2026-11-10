# Exemplo de uso do SILED

## 1. Entrar

Abra o endereço do sistema. Informe o CPF e a senha cadastrados. No campo **Unidade ou Órgão**, o administrador pode manter **UNIDADE CENTRAL INTEGRADA - Acesso geral**. O fiscalizador deve selecionar o seu órgão.

O administrador enxerga os processos de todos os órgãos. O fiscalizador pode cadastrar, consultar e editar os processos do órgão ao qual foi vinculado.

## 2. Cadastrar um processo

No menu lateral, clique em **Adicionar processo e arquivos**. Exemplo fictício para experimentar em uma instalação de testes:

| Campo | Exemplo |
| --- | --- |
| Código | Deixe vazio para gerar automaticamente. |
| Órgão | SESAU, se disponível para o seu perfil. |
| Prazo | Uma data futura para concluir a etapa. |
| Objeto | Aquisição demonstrativa de materiais de escritório. |
| Status | Recebido. |
| Risco | Baixo. |
| Modalidade | Pregão Eletrônico. |
| Percentual | 0. |
| Etapa atual | Triagem inicial. |
| Responsável | Nome do responsável pelo acompanhamento. |
| Valor estimado | `1.250,00`. |
| Ocorrência | Documentação recebida para conferência. |
| Encaminhamento | Conferir os documentos e registrar a análise. |

Selecione um arquivo de teste, se desejar, e clique em **Adicionar ao sistema**. O processo aparecerá no grupo **Recebidos**. O identificador automático usa ano e sequência do banco; não substitui um número oficial de processo.

## 3. Atualizar o andamento

No quadro, clique em **Conferir e editar** no processo. Altere a situação, a etapa, o percentual e os encaminhamentos. Clique em **Salvar alterações**.

A posição no quadro segue o campo **Status**. A alteração de percentual, sozinha, não troca a situação. Não existe arraste de cartões nesta versão, pois esse fluxo não foi demonstrado no vídeo de referência.

Se outra pessoa salvar o mesmo processo enquanto o formulário está aberto, o sistema solicita que você reabra a página antes de continuar, evitando sobrescrever uma atualização sem conferir.

## 4. Conferir anexos e exportar

Na edição, a seção **Arquivos já anexados** lista os downloads disponíveis ao seu perfil. Cada arquivo recebe um nome interno único, mesmo quando dois anexos têm o mesmo nome original.

No quadro central, **Exportar CSV** baixa os processos aos quais você tem acesso. Abra o arquivo no Excel. Caso a importação peça opções, use codificação UTF-8 e separador ponto e vírgula. Os anexos continuam no SILED; o CSV contém seus nomes.

## 5. Gerar o relatório mensal

Abra **Relatório mensal**, escolha o mês e clique em **Gerar relatório**. A síntese será salva no banco e poderá ser aberta novamente. Use **Imprimir** para abrir a impressão do navegador; a opção de salvar como PDF depende do navegador e do sistema operacional.

O filtro usa o mês da **última atualização** do processo, no horário de Porto Velho. Exemplo: um processo cadastrado em janeiro e editado em fevereiro entra na seleção de fevereiro após a edição. O relatório salvo anteriormente não é reescrito automaticamente. Gere novamente para atualizar a síntese do mês.

Os indicadores acima do menu mostram a posição atual de todos os processos visíveis. Os indicadores dentro do relatório usam o mês selecionado. Eles podem ter valores diferentes.

## 6. Usar os painéis superiores

- **Usuário:** nome, perfil, órgão e dados da conexão. O administrador encontra aqui **Gerenciar usuários**.
- **Registro de acesso:** últimas entradas e saídas. O administrador tem a visão geral; o fiscalizador vê os próprios registros.
- **Acessibilidade:** modos claro, escuro e contraste, tamanho do texto e redução de movimentos. A preferência fica no navegador utilizado.
- **Sair:** encerra a sessão do navegador.

O botão **Fechar barra de acesso** recolhe o menu lateral. Clique novamente para abrir.

## 7. Cadastrar outra pessoa

Entre como administrador e abra **Usuário → Gerenciar usuários**. Preencha nome, CPF, perfil, órgão e uma senha de 12 a 128 caracteres. Vincule cada fiscalizador ao órgão adequado.

Entregue o endereço do sistema e as credenciais por um canal privado. A pessoa só consegue entrar de outro local se o sistema estiver hospedado e acessível pela internet.

## 8. Recuperação de senha

Na entrada, **Recuperar senha** registra uma solicitação para o responsável. A resposta é a mesma para usuários existentes e inexistentes. Não há envio de e-mail nesta versão. O administrador verifica a identidade da pessoa e redefine a senha pelo terminal, conforme o guia de instalação.

## 9. Power BI

Sem configuração, a página informa que não existe painel conectado. Para incorporar um relatório permitido, o responsável configura no servidor:

```dotenv
POWERBI_EMBED_URL=https://app.powerbi.com/reportEmbed?reportId=SEU_RELATORIO
POWERBI_REPORT_TITLE=Nome do seu relatório
POWERBI_WORKSPACE_NAME=Nome do seu espaço de trabalho
```

O endereço acima é apenas um formato ilustrativo; não abre um relatório real. Use a URL de incorporação fornecida pelo Power BI e confirme as permissões. A conta SILED não concede acesso ao Power BI nem cria relatórios ou tokens. Não use **Publicar na Web** para documentos que precisem permanecer restritos.
