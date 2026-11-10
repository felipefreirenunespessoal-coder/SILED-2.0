"""Órgãos do projeto original e situações alinhadas aos grupos do quadro."""

ORGAOS = (
    "UNIDADE CENTRAL INTEGRADA - Acesso geral",
    "CASA CIVIL - Casa Civil", "CASA MILITAR - Casa Militar",
    "CGE - Controladoria Geral do Estado", "PGE - Procuradoria-Geral do Estado",
    "SEAGRI - Secretaria de Agricultura",
    "SEAS - Secretaria da Assistência e do Desenvolvimento Social",
    "SECOM - Secretaria de Comunicação", "SEDAM - Secretaria de Desenvolvimento Ambiental",
    "SEDEC - Secretaria de Desenvolvimento Econômico", "SEDUC - Secretaria de Educação",
    "SEFIN - Secretaria de Finanças", "SEGEP - Secretaria de Gestão de Pessoas",
    "SEJUCEL - Secretaria da Juventude, Cultura, Esporte e Lazer",
    "SEJUS - Secretaria de Justiça", "SEOSP - Secretaria de Obras e Serviços Públicos",
    "SEPAT - Secretaria de Patrimônio", "SEPOG - Secretaria de Planejamento, Orçamento e Gestão",
    "SESAU - Secretaria de Saúde", "SESDEC - Secretaria de Segurança, Defesa e Cidadania",
    "SETIC - Superintendência Estadual de Tecnologia da Informação e Comunicação",
    "SETUR - Superintendência Estadual de Turismo", "SUPEL - Superintendência Estadual de Licitações",
    "DETRAN - Departamento Estadual de Trânsito",
    "DER - Departamento Estadual de Estradas de Rodagem e Transportes",
    "IDARON - Agência de Defesa Sanitária Agrosilvopastoril",
    "IPERON - Instituto de Previdência dos Servidores Públicos do Estado",
    "POLITEC - Superintendência de Polícia Técnico-Científica",
    "PROCON - Programa Estadual de Defesa do Consumidor",
)
STATUS = ("Recebido", "Em análise", "Em acompanhamento", "Em alerta", "Concluído")
RISKS = ("Baixo", "Moderado", "Alto")
MODALITIES = ("Pregão Eletrônico", "Concorrência", "Dispensa Eletrônica", "Tomada de Preços", "Credenciamento", "Registro de Preços")
BOARD = (
    ("Recebido", "Recebidos", "Processos aguardando triagem inicial.", "recebidos"),
    ("Em análise", "Em análise", "Documentos e requisitos em conferência.", "analise"),
    ("Em acompanhamento", "Em acompanhamento", "Processos com monitoramento ativo.", "acompanhamento"),
    ("Em alerta", "Em alerta", "Pendências que exigem ação imediata.", "alerta"),
    ("Concluído", "Concluídos", "Fluxos encerrados no período.", "concluido"),
)
EXTENSIONS = {"csv", "doc", "docx", "jpeg", "jpg", "pdf", "png", "xls", "xlsx", "zip"}
