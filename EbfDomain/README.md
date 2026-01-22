# EBF Domain

Base domain classes for EBF trading system projects.

## Features

- Supports migration patterns with multiple ID types
- Zero external dependencies


## Installation
```bash
# Development mode (changes reflect immediately)
pip install -e .
```

## Usage
```python
from dataclasses import dataclass
from ebf_domain.id_base import IDBase

@dataclass(eq=False)
class Trade(IDBase[str]):
    symbol: str
    quantity: int

trade = Trade(symbol="B", quantity=100)
trade.resolve_id("TR-001")
```

## Testing
```bash
pytest tests/
```