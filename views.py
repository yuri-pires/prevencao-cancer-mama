
import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st
from dados import *

@st.cache_resource
def gera_grafico_mapa(df, indicador, ano):
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

def get_grafico_dispersao(por_uf_ano_dispersao, selecao_regiao):
    return (
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

def grafico_facet_por_ano(heatmap_infra, ordem_uf):
    """Gera um gráfico facetado por ano, com os valores do indicador por UF."""
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
    return grafico_facet

def get_grafico_linhas(serie_regiao):
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

    return linhas, linha_base


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

def get_grafico_barras(ranking, ano_ranking, ordem_ranking):
    """Gera um gráfico de barras com a variação percentual do indicador por estado em relação
    ao ano base."""
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

    return barras, linha_zero

def get_grafico_vazios(vazios, ordem_vazios):
    return (
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

def gera_grafico_pns(df):
    # 1. Gerar o gráfico para exames de mamografia
    fig_mamografia = px.bar(
        df,
        x='regiao',
        y='mamografia',
        color='regiao',
        color_discrete_map=PALETA_REGIAO | {"Brasil": "#ccc"},  # Mapeia as cores de acordo com a paleta definida    
        title='Mulheres selecionadas de 50 a 69 anos de idade que nunca realizaram exame de mamografia, por Região',
        labels={
            'regiao': 'Região',
            'mamografia': 'Quantidade de mulheres sem exames',
        },
        text_auto=True
    )

    fig_mamografia.update_layout(
        template='plotly_white',
        xaxis_title='Região',
        yaxis_title='Quantidade de mulheres sem exames'
    )

    # 2. Gerar o gráfico para exames de colo de útero
    fig_exames = px.bar(
        df,
        x='regiao',
        y='exames_colo',
        color='regiao',
        color_discrete_map=PALETA_REGIAO | {"Brasil": "#ccc"},  # Mapeia as cores de acordo com a paleta definida    
        title='Mulheres de 25 a 64 anos de idade que realizaram o exame preventivo para câncer de colo de útero nos últimos 3 anos anteriores à pesquisa, por Região',
        labels={
            'regiao': 'Região',
            'exames_colo': 'Mulheres que realizaram o exame nos últimos 3 anos',
        },
        text_auto=True
    )

    fig_exames.update_layout(
        title_text='Mulheres de 25 a 64 anos de idade que realizaram o exame preventivo para câncer de colo de útero<br> nos últimos 3 anos anteriores à pesquisa, por Região',
        template='plotly_white',
        xaxis_title='Região',
        yaxis_title='Quantidade de Exames'
    )
    
    return fig_mamografia, fig_exames