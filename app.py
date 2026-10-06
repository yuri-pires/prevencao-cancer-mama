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

import json

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# Configuração da página
# ============================================================

st.set_page_config(
    page_title="Prevenção do Câncer de Colo e Mama — Painel",
    page_icon="🎗️",
    layout="wide",
)

# --- Pasta onde os 8 CSVs (já extraídos dos .zip) estão salvos ---
DATA_DIR = "dados/"
GEOJSON_ESTADOS = "geojson/brasil_estados.json"

# --- Constantes usadas em várias seções ---
ANO_BASE = 2019    # último ano completo antes da pandemia
PERIODO_MAX_ALINHADO = 202512  # exclui o corte parcial de 2026 das comparações cruzadas

PALETA_REGIAO = {
    "Norte": "#1f77b4",
    "Nordeste": "#ff7f0e",
    "Centro-Oeste": "#2ca02c",
    "Sudeste": "#d62728",
    "Sul": "#9467bd",
}

FONTE = "Ministério da Saúde — Portal de Dados Abertos do SUS, painel MGDI (dados de 2016 a 2025)"

# --- Rótulos dos 8 indicadores do dataset, usados no seletor do mapa ---
CATEGORIAS = {
    "exames_cito": "Exames citopatológicos",
    "mamografias": "Mamografias",
    "hosp_alta_compl": "Hospitais habilitados (alta complexidade)",
    "hosp_persus": "Hospitais com licença PERSUS",
    "lab_qualicito": "Laboratórios QualiCito habilitados",
    "recursos_radio": "Recursos PERSUS para radioterapia",
    "servico_sdm": "Serviços de diagnóstico de mama (SDM)",
    "servico_src": "Serviços diag./trat. colo do útero (SRC)",
}


def fmt_milhar(n):
    """Formata um inteiro com separador de milhar no padrão pt-BR (ex.: 55702 -> '55.702')."""
    return f"{n:,.0f}".replace(",", ".")


# ============================================================
# Carregamento e preparação dos dados
# ============================================================

INDICADORES = pd.DataFrame([
    {"arquivo": "ccmec25a64.csv", "alias": "exames_cito",     "label": CATEGORIAS["exames_cito"]},
    {"arquivo": "ccmec50a69.csv", "alias": "mamografias",     "label": CATEGORIAS["mamografias"]},
    {"arquivo": "ccmhhcac.csv",   "alias": "hosp_alta_compl", "label": CATEGORIAS["hosp_alta_compl"]},
    {"arquivo": "ccmhpersus.csv", "alias": "hosp_persus",     "label": CATEGORIAS["hosp_persus"]},
    {"arquivo": "ccmqucito.csv",  "alias": "lab_qualicito",   "label": CATEGORIAS["lab_qualicito"]},
    {"arquivo": "ccmrftradi.csv", "alias": "recursos_radio",  "label": CATEGORIAS["recursos_radio"]},
    {"arquivo": "ccmsdmh.csv",    "alias": "servico_sdm",     "label": CATEGORIAS["servico_sdm"]},
    {"arquivo": "ccmsrch.csv",    "alias": "servico_src",     "label": CATEGORIAS["servico_src"]},
])

INDICADORES_INFRA = ["hosp_alta_compl", "hosp_persus", "lab_qualicito"]

COLUNAS_DESCRITIVAS = ["co_ibge", "co_anomes", "no_municipio", "sg_uf", "no_regiao_brasil"]


@st.cache_data
def carregar_dados():
    """Lê os 8 arquivos originais e devolve um único DataFrame município-ano, no mesmo
    formato usado na Atividade 01."""
    dados_brutos = {}
    for _, meta in INDICADORES.iterrows():
        caminho = DATA_DIR + meta["arquivo"]
        try:
            dados_brutos[meta["alias"]] = pd.read_csv(caminho, encoding="utf-8")
        except UnicodeDecodeError:
            dados_brutos[meta["alias"]] = pd.read_csv(caminho, encoding="latin-1")

    primeiro_alias = INDICADORES.iloc[0]["alias"]
    df = dados_brutos[primeiro_alias][COLUNAS_DESCRITIVAS + ["vl_indicador_calculado_mun"]].rename(
        columns={"vl_indicador_calculado_mun": primeiro_alias}
    )

    for _, meta in INDICADORES.iloc[1:].iterrows():
        df_valor = dados_brutos[meta["alias"]][["co_ibge", "co_anomes", "vl_indicador_calculado_mun"]].rename(
            columns={"vl_indicador_calculado_mun": meta["alias"]}
        )
        df = pd.merge(df, df_valor, on=["co_ibge", "co_anomes"], how="outer")

    df = df[df["co_anomes"] <= PERIODO_MAX_ALINHADO].copy()
    df["ano"] = df["co_anomes"] // 100  # extrai o ano de AAAAMM (ex.: 202512 -> 2025)
    return df


@st.cache_resource
def get_dados_estados():
    """Cacheada como resource (não data): evita recopiar os 14,5 MB de geometria a
    cada rerun do script, já que o GeoJSON é só leitura e não é mutado."""
    return json.load(open(GEOJSON_ESTADOS))


df = carregar_dados()

ANO_MIN, ANO_MAX = int(df["ano"].min()), int(df["ano"].max())
REGIOES = sorted(df["no_regiao_brasil"].dropna().unique())

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


@st.cache_resource
def gera_grafico_mapa(indicador, ano):
    """Cacheada como resource: a figura Plotly resultante é pesada (carrega o GeoJSON
    inteiro) e não precisa ser recopiada a cada rerun, só reconstruída quando o
    indicador ou o ano selecionados mudam. Um único ano por figura (sem
    animation_frame) evita que o Plotly revalide o GeoJSON contra 10 quadros de uma
    vez — isso sozinho reduziu o tempo de construção de ~6s para ~0,6s."""
    estados = get_dados_estados()

    por_estado_ano = (
        df[df["ano"] == ano].groupby("sg_uf")[list(CATEGORIAS.keys())].sum().reset_index()
    )

    mapa = px.choropleth_map(
        por_estado_ano,
        geojson=estados,
        locations="sg_uf",
        color=indicador,
        color_continuous_scale="Viridis",
        map_style="carto-positron",
        zoom=3,
        center={"lat": -14, "lon": -55},
        opacity=0.5,
        labels={"sg_uf": "Estado"} | CATEGORIAS,
        height=600,
    )
    mapa.update_geos(fitbounds="locations", visible=False)
    mapa.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, dragmode=False)
    return mapa

st.plotly_chart(
    gera_grafico_mapa(indicador_mapa, ano_mapa),
    width="stretch",
    config={"scrollZoom": False, "displayModeBar": False, "doubleClick": False},
)
st.caption(
    f"Fonte: {FONTE}. Soma do indicador por estado no ano selecionado ({ano_mapa}). "
    "Este mapa considera todos os estados do Brasil, independente dos filtros de "
    "período e região da barra lateral."
)

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

    dispersao = (
        alt.Chart(por_uf_ano_dispersao)
        .mark_circle(size=70)
        .encode(
            x=alt.X("recursos_radio:Q", title="Recurso de radioterapia (R$, escala log)", scale=alt.Scale(type="log")),
            y=alt.Y("exames_cito:Q", title="Exames citopatológicos (soma no ano)"),
            color=alt.Color(
                "Região:N",
                scale=alt.Scale(domain=list(PALETA_REGIAO.keys()), range=list(PALETA_REGIAO.values())),
            ),
            opacity=alt.condition(selecao_regiao, alt.value(0.85), alt.value(0.08)),
            tooltip=[
                alt.Tooltip("sg_uf:N", title="UF"),
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("Região:N"),
                alt.Tooltip("recursos_radio:Q", title="Recurso (R$)", format=",.0f"),
                alt.Tooltip("exames_cito:Q", title="Exames", format=",.0f"),
            ],
        )
        .add_params(selecao_regiao)
        .properties(height=450)
        .interactive()
    )

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

grafico_facet = (
    alt.Chart(heatmap_infra)
    .mark_rect()
    .encode(
        x=alt.X("ano:O", title="Ano"),
        y=alt.Y("sg_uf:N", sort=ordem_uf, title="Estado (UF)"),
        color=alt.Color(
            "presente:N",
            title="Habilitado?",
            scale=alt.Scale(domain=[0, 1], range=["#eaeaea", "#1f4e79"]),
            legend=alt.Legend(labelExpr="datum.label == '1' ? 'Sim' : 'Não'"),
        ),
        tooltip=[
            alt.Tooltip("sg_uf:N", title="UF"),
            alt.Tooltip("ano:O", title="Ano"),
            alt.Tooltip("indicador_label:N", title="Indicador"),
            alt.Tooltip("presente:N", title="Habilitado (1=sim, 0=não)"),
        ],
    )
    .properties(width=180, height=max(400, 18 * len(ordem_uf)))
    .facet(column=alt.Column("indicador_label:N", title=None))
    .resolve_scale(x="shared")
)

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
    linhas = (
        alt.Chart(serie_regiao)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("ano:O", title="Ano"),
            y=alt.Y("indice:Q", title=f"Índice ({ANO_BASE} = 100)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "Região:N",
                scale=alt.Scale(domain=list(PALETA_REGIAO.keys()), range=list(PALETA_REGIAO.values())),
            ),
            tooltip=[
                alt.Tooltip("Região:N"),
                alt.Tooltip("ano:O", title="Ano"),
                alt.Tooltip("indice:Q", title=f"Índice ({ANO_BASE} = 100)", format=".1f"),
                alt.Tooltip("valor:Q", title="Volume no ano", format=",.0f"),
            ],
        )
    )
    linha_base = (
        alt.Chart(pd.DataFrame({"y": [100]}))
        .mark_rule(strokeDash=[6, 4], color="#666")
        .encode(y="y:Q")
    )
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


def indice_por_estado(base_df, indicador, ano):
    """Soma o indicador por estado em ANO_BASE e em `ano` e devolve a variação percentual
    entre os dois (apenas estados com volume > 0 em ANO_BASE)."""
    por_uf = (
        base_df[base_df["ano"].isin([ANO_BASE, ano])]
        .groupby(["sg_uf", "ano"])[indicador]
        .sum()
        .unstack("ano")
    )
    if ANO_BASE not in por_uf.columns or ano not in por_uf.columns:
        return pd.DataFrame(columns=["sg_uf", "Região", "base", "valor", "indice", "variacao"])
    por_uf = por_uf[por_uf[ANO_BASE] > 0]
    regiao_uf = base_df.dropna(subset=["no_regiao_brasil"]).groupby("sg_uf")["no_regiao_brasil"].first()
    resultado = pd.DataFrame({
        "base": por_uf[ANO_BASE],
        "valor": por_uf[ano],
        "Região": regiao_uf.reindex(por_uf.index),
    })
    resultado["indice"] = resultado["valor"] / resultado["base"] * 100
    resultado["variacao"] = resultado["indice"] - 100
    return resultado.reset_index()


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
    barras = (
        alt.Chart(ranking)
        .mark_bar()
        .encode(
            x=alt.X("variacao:Q", title=f"Variação em {ano_ranking} vs {ANO_BASE} (%)"),
            y=alt.Y("sg_uf:N", sort=ordem_ranking, title="Estado (UF)"),
            color=alt.Color(
                "Região:N",
                scale=alt.Scale(domain=list(PALETA_REGIAO.keys()), range=list(PALETA_REGIAO.values())),
            ),
            tooltip=[
                alt.Tooltip("sg_uf:N", title="UF"),
                alt.Tooltip("Região:N"),
                alt.Tooltip("variacao:Q", title="Variação (%)", format="+.1f"),
                alt.Tooltip("base:Q", title=f"Volume em {ANO_BASE}", format=",.0f"),
                alt.Tooltip("valor:Q", title=f"Volume em {ano_ranking}", format=",.0f"),
            ],
        )
    )
    linha_zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#666").encode(x="x:Q")
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


@st.cache_resource
def gera_mapa_recuperacao(indicador, ano):
    """Cacheada como resource pelo mesmo motivo do mapa da View 1 (GeoJSON pesado);
    só é reconstruída quando o indicador ou o ano final do período mudam."""
    estados = get_dados_estados()
    dados_mapa = indice_por_estado(df, indicador, ano)
    if dados_mapa.empty:
        return None
    limite = max(abs(dados_mapa["variacao"].min()), abs(dados_mapa["variacao"].max()))
    mapa = px.choropleth_map(
        dados_mapa,
        geojson=estados,
        locations="sg_uf",
        color="variacao",
        color_continuous_scale="RdBu",
        range_color=(-limite, limite),
        color_continuous_midpoint=0,
        map_style="carto-positron",
        zoom=3,
        center={"lat": -14, "lon": -55},
        opacity=0.65,
        labels={"sg_uf": "Estado", "variacao": f"Variação vs {ANO_BASE} (%)"},
        hover_data={"valor": ":,.0f", "base": ":,.0f", "variacao": ":+.1f"},
        height=600,
    )
    mapa.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, dragmode=False)
    return mapa


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
    grafico_vazios = (
        alt.Chart(vazios)
        .mark_bar()
        .encode(
            x=alt.X("pct_sem_exame:Q", title="Municípios sem nenhum exame (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("sg_uf:N", sort=ordem_vazios, title="Estado (UF)"),
            color=alt.Color(
                "Região:N",
                scale=alt.Scale(domain=list(PALETA_REGIAO.keys()), range=list(PALETA_REGIAO.values())),
            ),
            tooltip=[
                alt.Tooltip("sg_uf:N", title="UF"),
                alt.Tooltip("Região:N"),
                alt.Tooltip("pct_sem_exame:Q", title="Sem exame (%)", format=".1f"),
                alt.Tooltip("sem_exame:Q", title="Municípios sem exame", format=",.0f"),
                alt.Tooltip("municipios:Q", title="Total de municípios", format=",.0f"),
            ],
        )
        .properties(height=max(400, 18 * len(vazios)))
    )
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
