from .comando import Agendador, ComandoComposto
from .comandos import CarregarTabela

CARGAS = [
    # --- nível 1 ---
    CarregarTabela(
        "itsm.fila",
        ["id_fila", "cd_fila", "nm_fila", "ds_descricao", "fl_ativo",
         "dt_inclusao", "dt_atualizacao", "nm_sistema_origem",
         "cd_registro_origem"],
    ),
    CarregarTabela(
        "itsm.categoria",
        ["id_categoria", "cd_categoria", "nm_categoria", "ds_descricao",
         "fl_ativo", "dt_inclusao", "dt_atualizacao",
         "nm_sistema_origem", "cd_registro_origem"],
    ),
    CarregarTabela(
        "itsm.sla",
        ["id_sla", "cd_sla", "nm_sla", "qt_meta_minutos", "ds_descricao",
         "fl_ativo", "dt_inclusao", "dt_atualizacao", "nm_sistema_origem",
         "cd_registro_origem"],
    ),
    CarregarTabela(
        "itsm.cliente_organizacao",
        ["id_cliente_organizacao", "cd_cliente_organizacao",
         "nm_cliente_organizacao", "nr_cnpj", "fl_ativo", "dt_inclusao",
         "dt_atualizacao", "nm_sistema_origem", "cd_registro_origem"],
    ),

    # --- nível 2 ---
    CarregarTabela(  # id_fila_atual → itsm.fila
        "itsm.analista",
        ["id_analista", "cd_analista", "nm_analista", "ds_email", "ds_nivel",
         "id_fila_atual", "fl_ativo", "dt_inclusao", "dt_atualizacao",
         "nm_sistema_origem", "cd_registro_origem"],
    ),
    CarregarTabela(  # id_cliente_organizacao → itsm.cliente_organizacao
        "itsm.solicitante",
        ["id_solicitante", "cd_solicitante", "id_cliente_organizacao",
         "nm_solicitante", "ds_email", "ds_telefone", "fl_ativo",
         "dt_inclusao", "dt_atualizacao", "nm_sistema_origem",
         "cd_registro_origem"],
    ),
    CarregarTabela(  # depende das quatro dimensões acima
        "itsm.chamado",
        ["id_chamado", "nr_chamado", "ds_tipo_chamado", "ds_status_chamado",
         "ds_prioridade", "dt_criacao", "dt_resolucao", "dt_ultima_atualizacao",
         "id_analista_atual", "id_reporter", "id_categoria",
         "id_cliente_organizacao", "id_fila_atual", "ds_titulo", "ds_descricao",
         "dt_inclusao", "dt_atualizacao", "nm_sistema_origem",
         "cd_registro_origem"],
    ),

    # --- nível 3 ---
    CarregarTabela(  # id_chamado → itsm.chamado, id_sla → itsm.sla
        "itsm.chamado_sla",
        ["id_chamado_sla", "id_chamado", "id_sla", "fl_breach",
         "qt_tempo_restante_minutos", "qt_tempo_decorrido_minutos",
         "qt_meta_minutos", "dt_referencia", "dt_inclusao", "dt_atualizacao",
         "nm_sistema_origem", "cd_registro_origem"],
    ),
    CarregarTabela(  # id_chamado → itsm.chamado
        "itsm.chamado_status_historico",
        ["id_chamado_status_historico", "id_chamado", "ds_status_chamado",
         "dt_inicio_status", "dt_fim_status", "qt_tempo_status_minutos",
         "id_analista_responsavel", "id_fila", "dt_inclusao", "dt_atualizacao",
         "nm_sistema_origem", "cd_registro_origem"],
    ),
    CarregarTabela(  # id_chamado → itsm.chamado, id_analista → itsm.analista
        "itsm.csat_avaliacao",
        ["id_csat_avaliacao", "id_chamado", "id_analista", "nr_score",
         "ds_comentario", "dt_avaliacao", "dt_inclusao", "dt_atualizacao",
         "nm_sistema_origem", "cd_registro_origem"],
    ),
]

AGENDADOR = Agendador()

for _carga in CARGAS:
    AGENDADOR.registrar(_carga)

AGENDADOR.registrar(ComandoComposto("carga_itsm", CARGAS))
