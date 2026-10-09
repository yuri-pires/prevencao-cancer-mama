# ============================================================
# Preparação do ambiente
# ============================================================
import pandas as pd              # manipulação e agregação dos dados
import streamlit as st          # biblioteca para criar dashboards interativos
import json                     # leitura do GeoJSON dos estados

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


# Dados da Pesquisa Nacional de Saúde (PNS) 2019, que não estão no dataset principal, mas são usados em algumas análises
# Mulheres de 25 a 64 anos de idade que realizaram o exame preventivo para câncer de colo de útero nos últimos 3 anos anteriores à pesquisa
# Mulheres selecionadas de 50 a 69 anos de idade que nunca realizaram exame de mamografia
def carregar_dados_pns():
    # 1. Ler os arquivos CSV
    df_mamo = pd.read_csv('dados_pns/nenhum_exame_mamografia.csv', sep=';', encoding='utf-8-sig')
    df_exames = pd.read_csv('dados_pns/exames_colo_utero.csv', sep=';', encoding='utf-8-sig')

    # 2. Renomear a coluna 'total' de cada um para identificar a categoria
    df_mamo = df_mamo.rename(columns={'mulheres_sem_exames': 'mamografia'})
    df_exames = df_exames.rename(columns={'exames_colo': 'exames_colo'})

    # 3. Unir os DataFrames pela coluna 'regiao'
    df_final = pd.merge(df_mamo, df_exames, on='regiao', how='outer').fillna(0)

    return df_final