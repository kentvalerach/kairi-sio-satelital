import sys
import os

# Asegurar que la raiz del proyecto este en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar la app principal
from dashboard.app import *