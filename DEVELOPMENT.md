"""Development guide for epub-converter project.

This file contains setup instructions, development workflows, and conventions.
"""

# DEVELOPMENT GUIDE

## Setup

### Prerequisites

- Python 3.12+
- pip or uv

### Installation

```bash
# Install the project in development mode
pip install -e .

# Or with uv
uv pip install -e .

# Install development dependencies
pip install pytest pytest-cov mypy black ruff
```

### Running the CLI

```bash
# Display available commands
python -m epub_converter

# Load an EPUB file
python -m epub_converter load-epub path/to/file.epub

# Extract a chapter
python -m epub_converter extract-chapter path/to/file.epub 0
```

---

## Code Style and Linting

### Type Checking

```bash
# Run mypy on the project
mypy src/epub_converter
```

### Formatting

```bash
# Format with black
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Run ruff
ruff check src/

# Fix issues automatically
ruff check --fix src/
```

### Combined Check

```bash
# Run all checks
./scripts/check.sh  # (to be created)
```

---

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/epub_converter

# Run specific test file
pytest tests/unit/domain/test_entities.py

# Run with verbose output
pytest -v
```

### Test Organization

```
tests/
├── unit/                          # Fast tests with mocks
│   ├── domain/
│   │   ├── epub_extraction/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_interfaces.py
│   │   └── ...
│   ├── application/
│   │   ├── epub_extraction/
│   │   │   ├── test_use_cases.py
│   │   │   ├── test_dtos.py
│   │   │   └── ...
│   ├── presentation/
│   │   └── cli/
│   │       ├── test_commands.py
│   │       └── test_controller.py
│   └── infrastructure/
│       └── epub_extraction/
│           └── test_repositories.py
├── integration/                   # Tests with real implementations
│   ├── infrastructure/
│   │   └── epub_extraction/
│   │       └── test_epub_repository_integration.py
│   └── end_to_end/
│       └── test_cli_flow.py
└── fixtures/                      # Test data and utilities
    ├── sample_epub_files/
    └── conftest.py
```

---

## Development Workflow

### Adding a New Feature

1. **Domain First**

   ```python
   # domain/my_feature/entities.py
   # domain/my_feature/value_objects.py
   # domain/my_feature/interfaces.py
   ```

   - Define domain entities and value objects
   - Write tests for domain logic

2. **Application Layer**

   ```python
   # application/my_feature/dtos.py
   # application/my_feature/use_cases.py
   # application/my_feature/interfaces.py
   ```

   - Create use cases using domain entities
   - Write tests for use cases (with mocks)

3. **Infrastructure**

   ```python
   # infrastructure/my_feature/repositories.py
   # infrastructure/my_feature/services.py
   ```

   - Implement domain interfaces
   - Write integration tests

4. **Presentation**

   ```python
   # presentation/cli/my_feature_commands.py
   ```

   - Create CLI commands
   - Write end-to-end tests

5. **Wire Dependencies**
   ```python
   # composition/container.py
   # Register commands and use cases
   ```

### Committing

Follow conventional commits:

```
feat(epub-extraction): add new chapter filtering capability
fix(cli): handle missing file paths gracefully
docs(architecture): update feature guide
test(application): improve use case test coverage
refactor(domain): rename ChapterId class
```

---

## Common Patterns

### Creating a Value Object

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MyValueObject:
    """Immutable value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate on creation."""
        if not self.value:
            raise ValueError("Value cannot be empty")
```

### Creating an Entity

```python
@dataclass
class MyEntity:
    """Mutable entity with identity."""

    id: MyEntityId
    name: str

    def perform_action(self) -> None:
        """Entities encapsulate business logic."""
        self.name = self.name.upper()
```

### Creating a Use Case

```python
class MyUseCase:
    """Use case orchestrates domain logic."""

    def __init__(self, repository: MyRepository) -> None:
        self.repository = repository

    def execute(self, input_dto: MyInput) -> MyOutput:
        """Execute business logic."""
        entity = self.repository.get(input_dto.id)
        entity.perform_action()
        self.repository.save(entity)
        return MyOutput.from_entity(entity)
```

### Creating a CLI Command

```python
class MyCommand(Command):
    """Framework-agnostic CLI command."""

    def __init__(self, use_case: MyUseCase) -> None:
        self._use_case = use_case

    @property
    def name(self) -> str:
        return "my-command"

    @property
    def description(self) -> str:
        return "Description of my command"

    def execute(self, *args, **kwargs) -> str:
        """Execute and return formatted output."""
        input_dto = MyInput(args[0])
        output_dto = self._use_case.execute(input_dto)
        return self._format_output(output_dto)

    def _format_output(self, output: MyOutput) -> str:
        """Format output for CLI."""
        return f"Result: {output.value}"
```

---

## IDE Setup

### VS Code

**Extensions:**

- Pylance (ms-python.pylance)
- Python (ms-python.python)
- Ruff (charliermarsh.ruff)

**Settings** (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "python.linting.ruffEnabled": true,
  "python.typeCheckingMode": "strict"
}
```

### PyCharm

- File → Settings → Project → Python Interpreter: Select Python 3.12
- File → Settings → Project → Python Integrated Tools: Enable pytest
- File → Settings → Editor → Code Style → Python: Set to Black

---

## Performance and Optimization

### Profiling

```bash
# Profile CPU usage
python -m cProfile -s cumtime -m epub_converter load-epub file.epub

# Use line_profiler for detailed analysis
pip install line_profiler
kernprof -l -v script.py
```

### Memory

```bash
# Check memory usage
pip install memory_profiler
python -m memory_profiler script.py
```

---

## Debugging

### Using pdb

```python
import pdb; pdb.set_trace()
```

### Using VS Code Debugger

1. Create `.vscode/launch.json`:

   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: CLI",
         "type": "python",
         "request": "launch",
         "module": "epub_converter",
         "args": ["load-epub", "sample.epub"]
       }
     ]
   }
   ```

2. Press F5 to debug

---

## CI/CD

### GitHub Actions (example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12"]

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}

      - run: pip install -e .
      - run: pip install pytest pytest-cov mypy black ruff
      - run: black --check src/ tests/
      - run: ruff check src/
      - run: mypy src/
      - run: pytest --cov
```

---

## Resources

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://www.domainlanguage.com/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
