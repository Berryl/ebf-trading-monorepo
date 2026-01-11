## Development Setup

```bash
# Create & activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install local domain & utils
pip install -e ../EbfDomain
pip install -e ../EbfUtil   # if needed

# Install project + dev tools
pip install -e .[dev]