"""
IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA
Atividade 02 — Dashboard interativo com Streamlit

Dashboard de continuidade da Atividade 01 (Prevenção do Câncer de Colo e Mama).
Views do painel:
  1. Mapa coroplético por estado, para os 8 indicadores do dataset (Plotly) — desenvolvido por Gabriel.
  2. Pergunta 5 (nova): recurso de radioterapia está associado a mais rastreamento? (Altair)
  3. Pergunta 6 (nova): a infraestrutura especializada cresceu de forma uniforme entre os estados? (Altair)
  4. Pergunta 7 (nova): o rastreamento já se recuperou do choque de 2020, por região? (Altair)

Público-alvo: gestor(a) de saúde municipal ou estadual, avaliando onde priorizar
investimento em rastreamento e em habilitação de novos serviços de referência.
"""

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st
from dados import *
from views import *

# ============================================================
# Configuração da página
# ============================================================

st.set_page_config(
    page_title="Prevenção do Câncer de Colo e Mama — Painel",
    page_icon="🎗️",
    layout="wide",
)


# ============================================================
# Barra lateral — filtros
# ============================================================

st.sidebar.header("Filtros")

periodo = st.sidebar.slider(
    "Período (anos)",
    min_value=ANO_MIN,
    max_value=ANO_MAX,
    value=(ANO_MIN, ANO_MAX),
)

regioes_selecionadas = st.sidebar.multiselect(
    "Regiões",
    options=REGIOES,
    default=REGIOES,
)

st.sidebar.divider()
st.sidebar.header("Filtro do mapa")
indicador_mapa = st.sidebar.selectbox(
    "Indicador",
    options=list(CATEGORIAS.keys()),
    format_func=lambda alias: CATEGORIAS[alias],
)
ano_mapa = st.sidebar.select_slider(
    "Ano do mapa",
    options=list(range(ANO_MIN, ANO_MAX + 1)),
    value=ANO_MAX,
)

st.sidebar.caption(f"Fonte dos dados: {FONTE}")

df_filtrado = df[
    (df["ano"] >= periodo[0])
    & (df["ano"] <= periodo[1])
    & (df["no_regiao_brasil"].isin(regioes_selecionadas))
]

df_pns = carregar_dados_pns()


# ============================================================
# Cabeçalho
# ============================================================

st.title("🎗️ Prevenção do Câncer de Colo e Mama — Painel de Acompanhamento")
st.markdown(
    "Painel voltado a **gestores de saúde municipal ou estadual**, para acompanhar a "
    "distribuição geográfica dos indicadores, a relação entre recurso de radioterapia e "
    "rastreamento, a evolução da infraestrutura especializada habilitada no SUS e a recuperação"
    " do rastreamento após a pandemia."
)

home, tab1, tab2, tab3, tab4 = st.tabs(["🏠 Início", "🗺️ Visualização Geográfica", "💲Infraestrutura e Recursos", "💉Impacto da pandemia", "📊 Ausência de exames"])

with home:
    st.markdown(
        "O câncer de colo do útero e o de mama podem ser detectados precocemente por exames de rastreamento, " \
        "mas o resultado depende também de uma rede de serviços capaz de confirmar o diagnóstico e iniciar o tratamento." \
        " Este painel apresenta uma análise visual e interativa dessa realidade no Brasil, voltada a gestores de saúde" \
        " municipais e estaduais que precisam decidir onde investir em rastreamento e na habilitação de novos serviços. " \
        
        "A análise também permite identificar estados com vazios assistenciais e comparar o ritmo de recuperação entre as regiões."
    )
    st.markdown(
        "O conjunto de dados reúne oito indicadores municipais do " \
        "Ministério da Saúde (Portal de Dados Abertos do SUS), de 2016 a 2025: exames citopatológicos, mamografias, hospitais " \
        "habilitados em alta complexidade, hospitais com licença PERSUS, laboratórios habilitados no QualiCito, recursos " \
        "de radioterapia e serviços de diagnóstico de mama e de colo do útero. Entre as perguntas levantadas exploramos se " \
        "os estados com recurso de radioterapia rastreiam mais, se a infraestrutura especializada cresceu de forma uniforme entre os estados" \
        " além de investigar se o rastreamento já se recuperou do choque de 2020 devido à pandemia de Covid-19." \
    )

    st.markdown(
        "As análises foram divididas de acordo com temas em comum nas categorias: **Visualização Geográfica**, " \
        " **Infraestrutura e Recursos**, **Impacto da pandemia** e **Ausência de exames**." \
    )

    st.header("Resumo do período selecionado")
    st.markdown(
        "O painel permite explorar os dados de 2016 a 2025, mas o período da barra lateral "
        "define quais anos são considerados nas análises. Abaixo, um resumo do volume total "
        "de exames e da presença de infraestrutura especializada nos estados, considerando "
        "apenas os anos e regiões selecionados."
    )
    
    resumo = (
        df_filtrado.groupby("sg_uf")[list(CATEGORIAS.keys())].sum().reset_index()
        .assign(
            hosp_alta_compl_presente=lambda x: (x["hosp_alta_compl"] > 0).astype(int),
            hosp_persus_presente=lambda x: (x["hosp_persus"] > 0).astype(int),
            lab_qualicito_presente=lambda x: (x["lab_qualicito"] > 0).astype(int),
        )
    )
    resumo["total_infra"] = resumo[["hosp_alta_compl_presente", "hosp_persus_presente", "lab_qualicito_presente"]].sum(axis=1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Exames citopatológicos", fmt_milhar(resumo["exames_cito"].sum()))
    col2.metric("Mamografias", fmt_milhar(resumo["mamografias"].sum()))
    col3.metric("Estados com as 3 infraestruturas habilitadas", f"{(resumo['total_infra'] == 3).sum()} de {len(resumo)}")


with tab1:

    if regioes_selecionadas == [] or df_filtrado.empty:
        st.warning("Nenhum dado para os filtros selecionados. Ajuste o período ou as regiões na barra lateral.")
        st.stop()

    # ============================================================
    # View 1 — Mapa coroplético por estado (Plotly)
    # ============================================================

    st.header("1. Como os indicadores se distribuem geograficamente entre os estados?")
    st.markdown(
        "Selecione um indicador e um ano na barra lateral (\"Filtro do mapa\") para ver sua "
        "distribuição por estado. Enquanto os demais gráficos deste painel mostram diferenças "
        "quantitativas, aqui é possível observar a concentração geográfica dos indicadores — "
        "em especial nas regiões Sul e Sudeste — o que ajuda a identificar desigualdades de "
        "cobertura no acesso a exames e serviços especializados."
    )

    st.plotly_chart(
        gera_grafico_mapa(df, indicador_mapa, ano_mapa),
        width="stretch",
        config={"scrollZoom": False, "displayModeBar": False, "doubleClick": False},
    )
    st.caption(
        f"Fonte: {FONTE}. Soma do indicador por estado no ano selecionado ({ano_mapa}). "
        "Este mapa considera todos os estados do Brasil, independente dos filtros de "
        "período e região da barra lateral."
    )

    fig_mamografia, fig_exames = gera_grafico_pns(df_pns)

    st.header("Dados complementares")
    st.markdown(
        "O painel também apresenta dados da Pesquisa Nacional de Saúde (PNS) 2019, realizada pelo IBGE," \
        " que traz informações sobre a realização de exames preventivos para câncer de colo do útero e mamografia." \
        " Os gráficos abaixo mostram a quantidade de mulheres que realizaram os exames preventivos de colo de útero até 3 anos antes da pesquisa e" \
        "do grupo de mulheres na faixa de 50 a 69 anos que nunca haviam realizado o exame de mamografia, divididos por região do Brasil."
    )
    st.markdown(
        "As informações resultantes da PNS 2019 oferecem valiosos subsídios à formulação" \
        " de políticas públicas nas áreas de promoção, vigilância e atenção à saúde do SUS," \
        " fomentando, assim, a resposta e o monitoramento de indicadores. "
    )

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(
                fig_mamografia,
                width="stretch",
            )

    with colB:
        st.plotly_chart(
            fig_exames,
            width="stretch",
        )
    
    st.caption(
        f"Fonte: IBGE - PNS (Pesquisa Nacional de Saúde). Didsponíveis no Sistema IBGE de Recuperação Automática - SIDRA, através da pesquisa do ano de 2019."
    )
with tab2:
    # ============================================================
    # View 2 — Pergunta 5 (nova): recurso de radioterapia está associado a mais rastreamento?
    # ============================================================
    # Pergunta que não foi respondida na Atividade 01: cruza dois indicadores (recurso
    # financeiro e volume de exames) para investigar se estados mais bem financiados em
    # radioterapia também rastreiam mais, por estado-ano.

    st.header("2. Estados que recebem mais recurso de radioterapia também rastreiam mais?")
    st.markdown(
        "Cada ponto é um **estado em um ano**: no eixo X, o recurso PERSUS de radioterapia recebido; "
        "no eixo Y, o volume de exames citopatológicos realizados. Clique numa região na legenda para "
        "destacar só os pontos dela."
    )

    por_uf_ano_dispersao = (
        df_filtrado.groupby(["ano", "sg_uf", "no_regiao_brasil"])[["recursos_radio", "exames_cito"]]
        .sum()
        .reset_index()
        .rename(columns={"no_regiao_brasil": "Região"})
    )
    por_uf_ano_dispersao = por_uf_ano_dispersao[por_uf_ano_dispersao["recursos_radio"] > 0]

    if por_uf_ano_dispersao.empty:
        st.info("Nenhum estado-ano com recurso de radioterapia > 0 para os filtros selecionados.")
    else:
        selecao_regiao = alt.selection_point(fields=["Região"], bind="legend")

        dispersao = (get_grafico_dispersao(por_uf_ano_dispersao, selecao_regiao))

        st.altair_chart(dispersao, width="stretch")
        st.caption(
            f"Fonte: {FONTE}. Unidade de análise: estado-ano, apenas estados com recurso de radioterapia > 0 no ano. "
            "Eixo X em escala logarítmica devido à forte concentração do recurso em poucos estados."
        )

        correlacao = por_uf_ano_dispersao[["recursos_radio", "exames_cito"]].corr().iloc[0, 1]
        st.markdown(
            f"**Correlação entre recurso de radioterapia e volume de exames:** {correlacao:.2f} "
            "(próximo de 0 indica que os dois indicadores variam de forma praticamente independente)."
        )

    # ============================================================
    # View 3 — Pergunta 6 (nova): a infraestrutura especializada cresceu de forma uniforme entre estados?
    # ============================================================
    # Pergunta que não foi respondida na Atividade 01: em vez de olhar um indicador de
    # infraestrutura por vez, compara os 3 (hospitais de alta complexidade, hospitais
    # PERSUS e laboratórios QualiCito) lado a lado, num heatmap por estado x ano, para ver
    # se a expansão foi concentrada em poucos estados ou distribuída pelo país.

    st.header("3. A infraestrutura especializada cresceu de forma uniforme entre os estados?")
    st.markdown(
        "Cada painel mostra a presença (habilitado/não habilitado) de **um tipo de infraestrutura** "
        "por estado e ano — hospitais de alta complexidade, hospitais com licença PERSUS e "
        "laboratórios QualiCito — para comparar se os três se expandiram no mesmo ritmo. "
        "Estados ordenados pelo total combinado dos três indicadores no período."
    )

    presenca_infra = (
        df_filtrado.groupby(["ano", "sg_uf"])[INDICADORES_INFRA]
        .max()
        .gt(0)
        .astype(int)
    )
    presenca_infra["score_infra"] = presenca_infra[INDICADORES_INFRA].sum(axis=1)
    presenca_infra = presenca_infra.reset_index()

    ordem_uf = (
        presenca_infra.groupby("sg_uf")["score_infra"].sum().sort_values(ascending=False).index.tolist()
    )

    detalhe_infra = INDICADORES.set_index("alias").loc[INDICADORES_INFRA, "label"]

    heatmap_infra = presenca_infra.melt(
        id_vars=["ano", "sg_uf"],
        value_vars=INDICADORES_INFRA,
        var_name="indicador",
        value_name="presente",
    )
    heatmap_infra["indicador_label"] = heatmap_infra["indicador"].map(detalhe_infra)

    grafico_facet = grafico_facet_por_ano(heatmap_infra, ordem_uf)

    st.altair_chart(grafico_facet, width="stretch")
    st.caption(
        f"Fonte: {FONTE}. Cada painel é um indicador binário (presença > 0 no estado-ano). "
        "Estados ordenados do maior para o menor total combinado dos três indicadores no período selecionado."
    )

    score_final = presenca_infra[presenca_infra["ano"] == periodo[1]].set_index("sg_uf")["score_infra"]
    sem_nenhuma_infra = score_final[score_final == 0]

    col1, col2 = st.columns(2)
    col1.metric(
        f"Estados com as 3 infraestruturas em {periodo[1]}",
        f"{(score_final == 3).sum()} de {len(score_final)}",
    )
    col2.metric(
        f"Estados sem nenhuma infraestrutura em {periodo[1]}",
        f"{len(sem_nenhuma_infra)} de {len(score_final)}",
    )

    if len(sem_nenhuma_infra) > 0:
        st.markdown(f"**Estados sem nenhuma infraestrutura habilitada em {periodo[1]}:** {', '.join(sorted(sem_nenhuma_infra.index))}")

with tab3:
    # ============================================================
    # View 4 — Pergunta 7 (nova): o rastreamento já se recuperou do choque de 2020?
    # ============================================================

    st.header("4. O rastreamento já se recuperou do choque de 2020?")
    st.markdown(
        f"Cada linha mostra o volume anual de exames de uma região **em relação a {ANO_BASE} "
        f"(= 100)**, último ano completo antes da pandemia. Abaixo de 100, a região ainda rastreia "
        "menos do que rastreava antes; acima, já superou a linha de base."
    )

    indicador_serie = st.radio(
        "Indicador",
        options=["exames_cito", "mamografias"],
        format_func=lambda alias: CATEGORIAS[alias],
        horizontal=True,
    )

    serie_regiao = (
        df[df["no_regiao_brasil"].isin(regioes_selecionadas)]
        .groupby(["ano", "no_regiao_brasil"])[indicador_serie]
        .sum()
        .reset_index()
        .rename(columns={"no_regiao_brasil": "Região", indicador_serie: "valor"})
    )
    base_regiao = serie_regiao[serie_regiao["ano"] == ANO_BASE].set_index("Região")["valor"]
    serie_regiao["indice"] = serie_regiao["valor"] / serie_regiao["Região"].map(base_regiao.where(base_regiao > 0)) * 100
    serie_regiao = serie_regiao[
        (serie_regiao["ano"] >= periodo[0]) & (serie_regiao["ano"] <= periodo[1])
    ].dropna(subset=["indice"])

    if serie_regiao.empty:
        st.info(f"Sem dados suficientes: o índice precisa de valores em {ANO_BASE} para as regiões selecionadas.")
    else:

        linhas, linha_base = get_grafico_linhas(serie_regiao)
        st.altair_chart((linha_base + linhas).properties(height=420), width="stretch")
        st.caption(
            f"Fonte: {FONTE}. Soma anual de {CATEGORIAS[indicador_serie].lower()} por região, dividida pelo "
            f"valor de {ANO_BASE} da mesma região. A linha tracejada marca o nível pré-pandemia."
        )

        ultimo_ano_serie = int(serie_regiao["ano"].max())
        if periodo[0] <= ANO_BASE <= ultimo_ano_serie:
            st.markdown(f"**Situação em {ultimo_ano_serie} em relação a {ANO_BASE}:**")
            ultimo = serie_regiao[serie_regiao["ano"] == ultimo_ano_serie].set_index("Região")["indice"]
            colunas = st.columns(len(ultimo))
            for coluna, (regiao, indice) in zip(colunas, ultimo.items()):
                coluna.metric(regiao, f"{indice:.0f}", f"{indice - 100:+.0f}% vs {ANO_BASE}")

    # ============================================================
    # View 5 — Ranking de estados pelo índice de recuperação (Altair)
    # ============================================================
    # A View 4 agrega por região e esconde a variação interna: aqui o mesmo índice
    # (ANO_BASE = 100) é calculado por estado, para apontar quais UFs priorizar.

    st.header("5. Quais estados mais se afastaram do nível pré-pandemia?")
    st.markdown(
        f"A View 4 mostra a recuperação por região; aqui o mesmo índice é aberto **por estado**, "
        f"ordenado da maior queda para a maior alta em relação a {ANO_BASE}. Barras à esquerda de zero "
        "indicam estados que ainda rastreiam menos do que antes da pandemia — candidatos a prioridade."
    )

    indicador_ranking = st.radio(
        "Indicador",
        options=["exames_cito", "mamografias"],
        format_func=lambda alias: CATEGORIAS[alias],
        horizontal=True,
        key="indicador_ranking",
    )

    ano_ranking = periodo[1]
    ranking = indice_por_estado(
        df[df["no_regiao_brasil"].isin(regioes_selecionadas)], indicador_ranking, ano_ranking
    )

    if ranking.empty:
        st.info(f"Sem dados suficientes: o índice precisa de valores em {ANO_BASE} e em {ano_ranking}.")
    else:
        ordem_ranking = ranking.sort_values("variacao")["sg_uf"].tolist()
        

        barras, linha_zero = get_grafico_barras(ranking, ano_ranking, ordem_ranking)
        st.altair_chart(
            (barras + linha_zero).properties(height=max(400, 18 * len(ranking))),
            width="stretch",
        )
        st.caption(
            f"Fonte: {FONTE}. Soma anual de {CATEGORIAS[indicador_ranking].lower()} por estado em {ano_ranking}, "
            f"comparada a {ANO_BASE}. Considera as regiões selecionadas na barra lateral e o fim do período "
            "como ano de comparação; estados sem volume em 2019 ficam de fora."
        )

        n_abaixo = int((ranking["variacao"] < 0).sum())
        pior = ranking.loc[ranking["variacao"].idxmin()]
        col1, col2 = st.columns(2)
        col1.metric(f"Estados abaixo do nível de {ANO_BASE}", f"{n_abaixo} de {len(ranking)}")
        col2.metric(f"Maior queda: {pior['sg_uf']}", f"{pior['variacao']:+.0f}%")

    # ============================================================
    # View 6 — Mapa de recuperação por estado (Plotly)
    # ============================================================
    # A View 1 mostra volume absoluto, que reflete o tamanho da população. Aqui o mapa mostra a
    # variação em relação a ANO_BASE, que é comparável entre estados de tamanhos diferentes.

    st.header("6. Onde a recuperação do rastreamento está mais atrasada no território?")
    st.markdown(
        f"Mapa da variação percentual do volume de exames em relação a {ANO_BASE}, por estado. "
        "Tons de **vermelho** indicam queda (rastreia menos que antes da pandemia) e tons de **azul**, "
        "alta. Diferente do mapa da seção 1, a cor não depende do tamanho da população do estado."
    )

    indicador_mapa_rec = st.radio(
        "Indicador",
        options=["exames_cito", "mamografias"],
        format_func=lambda alias: CATEGORIAS[alias],
        horizontal=True,
        key="indicador_mapa_recuperacao",
    )

    mapa_recuperacao = gera_mapa_recuperacao(indicador_mapa_rec, periodo[1])
    if mapa_recuperacao is None:
        st.info(f"Sem dados suficientes: o índice precisa de valores em {ANO_BASE} e em {periodo[1]}.")
    else:
        st.plotly_chart(
            mapa_recuperacao,
            width="stretch",
            config={"scrollZoom": False, "displayModeBar": False, "doubleClick": False},
        )
        st.caption(
            f"Fonte: {FONTE}. Variação de {CATEGORIAS[indicador_mapa_rec].lower()} entre {ANO_BASE} e {periodo[1]} "
            "(fim do período da barra lateral). Este mapa considera todos os estados, independente do filtro de região."
        )

with tab4:
    # ============================================================
    # View 7 — Vazios assistenciais: municípios sem nenhum exame (Altair)
    # ============================================================
    # Os CSVs são municipais, mas as views anteriores somam por estado. Aqui a unidade volta a
    # ser o município: qual a parcela deles que não registrou nenhum exame no ano?

    st.header("7. Em quantos municípios não há nenhuma produção de exames registrada?")
    st.markdown(
        "Um estado pode ter um volume total alto e concentrá-lo em poucos municípios. Cada barra mostra a "
        "**parcela de municípios sem nenhum exame registrado** no ano, por estado — ou seja, onde a "
        "população precisa se deslocar para outro município para ser rastreada."
    )

    col_ind, col_ano = st.columns([2, 3])
    indicador_vazio = col_ind.radio(
        "Indicador",
        options=["exames_cito", "mamografias"],
        format_func=lambda alias: CATEGORIAS[alias],
        key="indicador_vazio",
    )
    ano_vazio = col_ano.select_slider(
        "Ano",
        options=list(range(ANO_MIN, ANO_MAX + 1)),
        value=periodo[1] if ANO_MIN <= periodo[1] <= ANO_MAX else ANO_MAX,
        key="ano_vazio",
    )

    municipios_ano = df[
        (df["ano"] == ano_vazio)
        & (df["no_regiao_brasil"].isin(regioes_selecionadas))
        & df[indicador_vazio].notna()
    ]
    vazios = (
        municipios_ano.assign(sem_exame=municipios_ano[indicador_vazio] == 0)
        .groupby(["sg_uf", "no_regiao_brasil"])
        .agg(municipios=("co_ibge", "nunique"), sem_exame=("sem_exame", "sum"))
        .reset_index()
        .rename(columns={"no_regiao_brasil": "Região"})
    )
    vazios["pct_sem_exame"] = vazios["sem_exame"] / vazios["municipios"] * 100

    if vazios.empty:
        st.info("Nenhum município com dados para os filtros selecionados.")
    else:
        ordem_vazios = vazios.sort_values("pct_sem_exame", ascending=False)["sg_uf"].tolist()

        grafico_vazios = get_grafico_vazios(vazios, ordem_vazios)

        st.altair_chart(grafico_vazios, width="stretch")
        st.caption(
            f"Fonte: {FONTE}. Município sem exame = valor do indicador igual a zero em {ano_vazio}. "
            "A parcela de zeros é praticamente estável ao longo da série (cerca de 89% dos municípios para "
            "citopatológicos), o que sugere que o indicador municipal conta exames onde foram realizados, e não "
            "onde a paciente mora: zero indica município sem prestador, não necessariamente população sem rastreamento."
        )

        total_mun = int(vazios["municipios"].sum())
        total_sem = int(vazios["sem_exame"].sum())
        col1, col2 = st.columns(2)
        col1.metric(f"Municípios sem produção em {ano_vazio}", f"{fmt_milhar(total_sem)} de {fmt_milhar(total_mun)}")
        col2.metric("Parcela do total", f"{total_sem / total_mun * 100:.1f}%")