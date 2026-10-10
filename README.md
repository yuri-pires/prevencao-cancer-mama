# Prevenção do Câncer de Colo e Mama — Painel de Acompanhamento

IA001 — Análise e Visualização de Dados com Python e Ferramentas Assistidas por IA
Atividade 02 — Dashboard interativo com Streamlit

**Autores:** Yuri Espinosa e Gabriel Fernandes

**Acesse o painel online:** [painel-prevencao-cancer-mama.streamlit.app](https://painel-prevencao-cancer-mama.streamlit.app/)

Dashboard de continuidade da Atividade 01, voltado a gestores de saúde municipal ou
estadual, que acompanha o rastreamento do câncer de colo do útero e de mama no Brasil
entre 2016 e 2025. O painel é organizado em 5 abas e 7 views:

| Aba | View | Descrição |
|---|---|---|
| 🏠 Início | — | Apresentação do painel, resumo do período selecionado (exames, mamografias, infraestrutura) e orientação de uso. |
| 🗺️ Visualização Geográfica | 1 | **Mapa coroplético por estado** (Plotly): distribuição de qualquer um dos 8 indicadores, com seletor de indicador e de ano. Inclui dados complementares da PNS 2019 (gráficos de barras por região). |
| 💲 Infraestrutura e Recursos | 2 | **Dispersão recurso de radioterapia × exames citopatológicos** (Altair): estados mais financiados rastreiam mais? Mostra também a correlação. |
| | 3 | **Heatmap de infraestrutura especializada** (Altair): cobertura de hospitais de alta complexidade, hospitais PERSUS e laboratórios QualiCito, por estado e ano. |
| 💉 Impacto da pandemia | 4 | **Série temporal indexada** (Altair): volume anual de exames por região, com 2019 = 100, para ver a recuperação após 2020. |
| | 5 | **Ranking de estados** (Altair): variação do volume de exames de cada estado em relação a 2019. |
| | 6 | **Mapa de recuperação** (Plotly): variação percentual por estado em relação a 2019, independente do tamanho da população. |
| 📊 Ausência de exames | 7 | **Vazios assistenciais** (Altair): parcela de municípios sem nenhuma produção de exames registrada, por estado e ano. |

Fonte dos dados: Ministério da Saúde — Portal de Dados Abertos do SUS, painel
[MGDI — Prevenção do Câncer de Colo e Mama](https://dadosabertos.saude.gov.br/dataset/mgdi-prevencao-do-cancer-de-colo-e-mama).
Os dados complementares de exames preventivos e mamografia vêm da Pesquisa Nacional de
Saúde (PNS) 2019.

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

Os 8 arquivos CSV do dataset MGDI estão na pasta `dados/`, os 2 arquivos da PNS 2019 em
`dados_pns/` e a geometria dos estados em `geojson/brasil_estados.json` (usada nos
mapas). Não é necessário baixar nada — basta manter a estrutura de pastas.

Cada CSV do MGDI corresponde a um dos 8 indicadores do painel, com uma linha por
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
se o município tinha ou não o serviço habilitado). O `dados.py` une os 8 arquivos pela
chave (município, ano) num único DataFrame antes de gerar as visualizações. O corte
parcial de 2026 é excluído para manter a comparação entre anos consistente.

Os arquivos da PNS 2019 (separador `;`) trazem, por região:

| Arquivo | Conteúdo |
|---|---|
| `exames_colo_utero.csv` | Mulheres de 25 a 64 anos que fizeram o preventivo de colo do útero nos 3 anos anteriores à pesquisa |
| `nenhum_exame_mamografia.csv` | Mulheres de 50 a 69 anos que nunca fizeram mamografia |

Caso precisem reobter os dados originais (por exemplo, para atualizar a série), a fonte
é o Ministério da Saúde — Portal de Dados Abertos do SUS, painel
[MGDI — Prevenção do Câncer de Colo e Mama](https://dadosabertos.saude.gov.br/dataset/mgdi-prevencao-do-cancer-de-colo-e-mama)
(8 recursos, cada um baixado como um `.zip`, que deve ser extraído em `dados/`).

### Observações sobre os dados

- **Ano-base:** as views de recuperação (4, 5 e 6) usam 2019, último ano completo antes
  da pandemia, como referência (= 100).
- **"Município sem exame" (view 7):** o indicador municipal conta os exames onde foram
  realizados, não onde a paciente mora. Zero indica município sem prestador, não
  necessariamente população sem rastreamento. A parcela de zeros é praticamente estável
  ao longo da série.
- **Base muito pequena:** estados com volume quase nulo em 2019 podem gerar variações
  percentuais extremas (por exemplo, mamografias no Amapá), o que distorce a escala de
  cores do mapa da view 6.

## Execução

Com o ambiente virtual ativado, rode:

```bash
streamlit run app.py
```

O Streamlit abre automaticamente uma aba no navegador (geralmente em
`http://localhost:8501`). Use os filtros na barra lateral (período, regiões, e
indicador e ano do mapa) para explorar as views.

## Estrutura do projeto

```
app.py                  # aplicação Streamlit: layout, abas e filtros
dados.py                # carregamento, constantes e preparação dos dados
views.py                # funções que geram os gráficos e mapas
requirements.txt        # dependências Python
README.md               # este arquivo
dados/                  # os 8 CSVs do dataset MGDI
dados_pns/              # CSVs da Pesquisa Nacional de Saúde 2019
geojson/
  brasil_estados.json   # geometria dos estados do Brasil, usada nos mapas
atividade02_*.ipynb     # notebook da Atividade 02 (registro do grupo)
```
