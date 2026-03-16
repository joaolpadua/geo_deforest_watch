"""
RASTER CACHE SYSTEM
===================

Esse módulo implementa um cache local para rasters Sentinel.

Problema:
---------

Sem cache, cada execução do pipeline faria download de:

    B04 (red)
    B08 (nir)
    SCL (scene classification)

Isso gera:

    • downloads repetidos
    • pipeline lento
    • risco de corrupção em paralelismo

Solução:
--------

Salvar rasters localmente e reutilizar.

Fluxo:

    URL raster
        ↓
    extrair nome do arquivo
        ↓
    verificar se já existe
        ↓
    se existir → usar
    se não → baixar
"""

from pathlib import Path
from urllib.parse import urlparse
import requests


# diretório onde os rasters serão armazenados
CACHE_DIR = Path("data/cache/sentinel")


def get_cached_raster(url):
    """
    Baixa um raster apenas se ele ainda não existir no cache.

    Parameters
    ----------
    url : str
        URL do raster no Planetary Computer.

    Returns
    -------
    str
        Caminho local do raster.
    """

    # cria pasta se não existir
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # remove tokens SAS da URL
    parsed = urlparse(url)

    # pega apenas o nome do arquivo
    filename = parsed.path.split("/")[-1]

    # caminho final
    local_path = CACHE_DIR / filename

    # se já existe → retorna
    if local_path.exists():
        return str(local_path)

    print(f"Downloading raster → {filename}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    # salva no disco
    with open(local_path, "wb") as f:

        for chunk in response.iter_content(8192):
            if chunk:
                f.write(chunk)

    return str(local_path)