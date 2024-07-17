# longplexpy

[![CI](https://github.com/seqwell/longplexpy/actions/workflows/python_package.yml/badge.svg?branch=main)](https://github.com/seqwell/longplexpy/actions/workflows/python_package.yml?query=branch%3Amain)
[![Python Versions](https://img.shields.io/badge/python-3.11_|_3.12-blue)](https://github.com/seqwell/longplexpy)
[![MyPy Checked](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)

## Local Installation

First install the Python packaging and dependency management tool [`poetry`](https://python-poetry.org/docs/#installation).
You must have Python 3.10 or greater available on your system path, which could be managed by [`pyenv`](https://github.com/pyenv/pyenv) or another package manager. 
Finally, install the dependencies of the project with:

```bash
poetry install
```

Use the longplexpy at the CLI:

```console
$ poetry run longplexpy hello --name Fulcrum
```

## Testing Installation

A test report can be generated with:
```
poetry run multiqc tests/data
```
