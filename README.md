# tinyos3
Highly experimental Python3 compatible TinyOS tools.

## Getting started with uv

This project now uses [uv](https://github.com/astral-sh/uv) for dependency
management. After installing `uv`, create a virtual environment and install the
runtime and development dependencies with:

```
uv sync
```

You can then run the test suite through uv:

```
uv run pytest
```

The runtime dependency footprint is intentionally small (just `pyserial`),
while the `pytest` dependency is tracked as a development-only dependency via
`tool.uv.dev-dependencies` in `pyproject.toml`.

## Description
Currently, the only Python tools avaialable on PyPI for TinyOS are Python2
compatible only. These tools are an attempt by myself to convert those tools
over to Python3 while still maintaining compatibility with Python2 TinyOS
Python applications.

The initial transformation from Python2 to Python3 was performed using the
Python tool '2to3'.

## Notes on the License
The TinyOS Python tools consist of contributions from many different individuals
from many different institutions both public and private. That said, there is
no license for the overall TinyOS Python tools distribution, as each contributor
uses a different license.

TinyOS is an open-source platform and as such each of the licenses in use
in the Python tools are open-source compatible licenses (usually a derivative
of the GPL license). For more information on these licenses, please refer to
the individual source file itself.
