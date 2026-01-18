#!/bin/bash

venv_name="venv"

# Crear el entorno si no existe
if [ ! -d ".$venv_name" ]; then
    python3 -m venv ".$venv_name"
fi

# Activar el entorno virtual
source ".$venv_name/bin/activate"

# Instalar dependencias
pip install -r requirements.txt