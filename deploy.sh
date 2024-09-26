# after deprecation of some arguments in 15.1.0
venv_name="venv"
echo $venv_name
virtualenv ".$venv_name" && source ".$venv_name/bin/activate" && pip install -r requirements.txt