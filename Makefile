.PHONY: help install run menu clean check compile venv list-servers setup

PYTHON   ?= python
PIP      ?= $(PYTHON) -m pip
VENV     ?= .venv
BIN      ?= $(VENV)/Scripts
PY       ?= $(if $(wildcard $(BIN)/python.exe),$(BIN)/python,$(PYTHON))

help:
	@echo Karuma — available targets:
	@echo.
	@echo   make setup          Copy examples/*.example to project root (skip existing)
	@echo   make install        Install dependencies into current Python
	@echo   make venv           Create .venv and install dependencies
	@echo   make run            Start interactive menu (alias: menu)
	@echo   make list-servers   List connected Discord servers
	@echo   make check          Compile all Python modules
	@echo   make clean          Remove caches and log files
	@echo.
	@echo Options (override on command line):
	@echo   PYTHON=python3 make run
	@echo   PY=.venv/Scripts/python make run

setup:
	$(PY) -c "import shutil; from pathlib import Path; \
pairs=[('config.json.example','config.json'),('tokens.txt.example','tokens.txt'),('proxies.txt.example','proxies.txt'),('members.txt.example','members.txt')]; \
[(print(f'skip {d} (exists)') if Path(d).exists() else (shutil.copy2(Path('examples')/s,d), print(f'created {d}'))) for s,d in pairs]"

install:
	$(PIP) install -r requirements.txt

venv: $(VENV)/Scripts/python.exe
	$(BIN)/python -m pip install -r requirements.txt

$(VENV)/Scripts/python.exe:
	$(PYTHON) -m venv $(VENV)

run menu:
	$(PY) -m karuma menu

list-servers:
	$(PY) -m karuma list-servers

check compile:
	$(PY) -m compileall -q karuma karuma.py pyfade

clean:
	$(PY) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink(missing_ok=True) for p in [pathlib.Path('karuma.log')]]"
