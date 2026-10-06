# Prevenção do Câncer de Colo e Mama — Painel de Acompanhamento

IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA
Atividade 02 — Dashboard interativo com Streamlit

Dashboard de continuidade da Atividade 01, voltado a gestores de saúde municipal ou
estadual, com 4 views:

1. **Mapa coroplético por estado** (Plotly) — distribuição geográfica de qualquer um
   dos 8 indicadores do dataset, com seletor de indicador e de ano.
2. **Dispersão recurso de radioterapia × exames citopatológicos** (Altair) — investiga
   se estados mais financiados em radioterapia também rastreiam mais.
3. **Heatmap de infraestrutura especializada** (Altair) — compara, estado a estado e
   ano a ano, a cobertura de hospitais de alta complexidade, hospitais PERSUS e
   laboratórios QualiCito.
4. **Série temporal indexada** (Altair) — volume anual de exames citopatológicos ou
   mamografias por região, com 2019 = 100, para ver a recuperação pós-pandemia.

Fonte dos dados: Ministério da Saúde — Portal de Dados Abertos do SUS, painel
[MGDI — Prevenção do Câncer de Colo e Mama](https://dadosabertos.saude.gov.br/dataset/mgdi-prevencao-do-cancer-de-colo-e-mama).

## Pré-requisitos

- Python 3.10 ou superior
- pip

## Instalação

1. Clone ou extraia esta pasta do projeto.
2. (Recomendado) Crie e ative um ambiente virtual:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   .venv\Scripts\activate           # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Dados

Os 8 arquivos CSV do dataset MGDI já estão incluídos nesta entrega, na pasta `dados/`,
assim como `geojson/brasil_estados.json` (geometria dos estados, usada no mapa
coroplético). Não é necessário baixar nada — basta manter a estrutura de pastas como
veio no ZIP/pasta entregue:

```
stream-lit-project/
├── app.py
├── requirements.txt
├── geojson/
│   └── brasil_estados.json
└── dados/
    ├── ccmec25a64.csv
    ├── ccmec50a69.csv
    ├── ccmhhcac.csv
    ├── ccmhpersus.csv
    ├── ccmqucito.csv
    ├── ccmrftradi.csv
    ├── ccmsdmh.csv
    └── ccmsrch.csv
```

Cada CSV corresponde a um dos 8 indicadores do painel MGDI, com uma linha por
município e ano (corte de dezembro, 2016–2025):

| Arquivo | Indicador | Tipo |
|---|---|---|
| `ccmec25a64.csv` | Exames citopatológicos (mulheres de 25 a 64 anos) | Fluxo (exames) |
| `ccmec50a69.csv` | Mamografias (mulheres de 50 a 69 anos) | Fluxo (exames) |
| `ccmhhcac.csv` | Hospitais habilitados de alta complexidade | Estoque (hospitais) |
| `ccmhpersus.csv` | Hospitais com licença PERSUS | Estoque (hospitais) |
| `ccmqucito.csv` | Laboratórios QualiCito habilitados | Estoque (laboratórios) |
| `ccmrftradi.csv` | Recursos PERSUS destinados à radioterapia | Fluxo (R$) |
| `ccmsdmh.csv` | Serviços de diagnóstico de mama (SDM) habilitados | Estoque (serviços) |
| `ccmsrch.csv` | Serviços de diagnóstico/tratamento do colo do útero (SRC) habilitados | Estoque (serviços) |

Indicadores de **fluxo** são somados no período (ex.: total de exames no ano);
indicadores de **estoque** representam presença/capacidade instalada naquele ano (ex.:
se o município tinha ou não o serviço habilitado). O `app.py` une os 8 arquivos pela
chave (município, ano) num único DataFrame antes de gerar as visualizações.

Caso precisem reobter os dados originais (por exemplo, para atualizar a série), a fonte
é o Ministério da Saúde — Portal de Dados Abertos do SUS, painel
[MGDI — Prevenção do Câncer de Colo e Mama](https://dadosabertos.saude.gov.br/dataset/mgdi-prevencao-do-cancer-de-colo-e-mama)
(8 recursos, cada um baixado como um `.zip`, que deve ser extraído em `dados/`).

## Execução

Com o ambiente virtual ativado, rode:

```bash
streamlit run app.py
```

O Streamlit abre automaticamente uma aba no navegador (geralmente em
`http://localhost:8501`). Use os filtros na barra lateral (período, regiões,
indicador e ano do mapa) para explorar as quatro views.

## Estrutura do projeto

```
app.py                 # aplicação Streamlit (única entrada do dashboard)
requirements.txt        # dependências Python
README.md               # este arquivo
dados/                  # os 8 CSVs do dataset MGDI (incluídos nesta entrega)
geojson/
  brasil_estados.json   # geometria dos estados do Brasil, usada no mapa coroplético
atividade02_*.ipynb      # notebook da Atividade 02 (registro do grupo)
```
