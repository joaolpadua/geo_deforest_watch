# 🌳 Geo Deforest Watch

Pipeline geoespacial para detecção de perda de vegetação (desmatamento)
utilizando imagens Sentinel-2 e análise temporal de NDVI.

------------------------------------------------------------------------

## 🚀 Objetivo

Detectar automaticamente áreas com possível desmatamento a partir de:

-   imagens de satélite (Sentinel-2)
-   cálculo de NDVI
-   análise temporal por célula espacial
-   identificação de quedas significativas de vegetação

------------------------------------------------------------------------

## 🧠 Como funciona

Pipeline:

AOI → Grid → Sentinel-2 → NDVI → Zonal Stats → Série Temporal → Detecção
→ Alertas

------------------------------------------------------------------------

## 📦 Tecnologias

-   Python
-   Rasterio
-   GeoPandas
-   NumPy
-   STAC API (Planetary Computer)
-   Matplotlib

------------------------------------------------------------------------

## 📊 Outputs

O sistema gera:

### 📄 CSV

Tabela com NDVI ao longo do tempo + alertas

### 🗺️ Mapas

Visualização espacial dos índices e alertas

### 🎬 GIF temporal

Evolução da vegetação ao longo do tempo

### 🌍 GeoJSON

Arquivo geoespacial com áreas detectadas

------------------------------------------------------------------------

## 🚨 Lógica de detecção

-   cálculo de variação NDVI por célula
-   identificação de quedas abruptas
-   verificação de persistência
-   classificação em níveis:
    -   NORMAL
    -   MÉDIO
    -   ALTO
    -   CRÍTICO

------------------------------------------------------------------------

## 💡 Aplicações

-   monitoramento ambiental
-   detecção de desmatamento
-   compliance ESG
-   análise de uso do solo
-   apoio a crédito rural

------------------------------------------------------------------------

## 📍 Status

✔ Pipeline funcional\
✔ Detecção implementada\
✔ Visualização temporal\
✔ Export geoespacial

------------------------------------------------------------------------

## 🔥 Próximos passos

-   integração com imagens base reais (satélite RGB)
-   dashboard interativo
-   API para análise sob demanda
-   sistema automatizado

------------------------------------------------------------------------

## 👨‍💻 Autor

Joao Luiz de Pádua

------------------------------------------------------------------------

Projeto desenvolvido como aplicação prática de Geoprocessamento +
Sensoriamento Remoto + Python.
