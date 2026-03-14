"""
Configuração global dos testes.

Este arquivo adiciona a pasta 'src' ao PYTHONPATH para que os
módulos do projeto possam ser importados durante os testes.
"""

import sys
from pathlib import Path

# Caminho até a raiz do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Adiciona a raiz do projeto ao path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))