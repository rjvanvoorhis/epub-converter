# Quick Developer Reference

## Project at a Glance

- **Architecture**: Clean Architecture with Vertical Feature Slices
- **Language**: Python 3.12+
- **Typing**: Full type hints using `typing.Protocol`
- **Features**: EPUB extraction, audiobook generation via VoiceBox API

## Directory Map

```
src/epub_converter/
├── domain/                  ← Business logic, no dependencies
│   ├── epub_extraction/     ← EPUB feature domain
│   └── audiobook_conversion/ ← Audiobook feature domain
├── application/             ← Use cases, orchestration
│   ├── epub_extraction/
│   └── audiobook_conversion/
├── infrastructure/          ← Concrete implementations
│   ├── epub_extraction/
│   └── audiobook_conversion/
├── presentation/            ← CLI commands
│   └── cli/
└── composition/             ← Dependency injection
    └── container.py
```

## Common Tasks

### 1. Add a New Use Case

1. Create domain entities/value objects in `domain/feature_name/entities.py`
2. Create domain interfaces in `domain/feature_name/interfaces.py`
3. Create DTOs in `application/feature_name/dtos.py`
4. Create use case protocol in `application/feature_name/interfaces.py`
5. Implement use case in `application/feature_name/use_cases.py`
6. Implement infrastructure services in `infrastructure/feature_name/`
7. Create presentation commands in `presentation/cli/feature_name_commands.py`
8. Wire in `composition/container.py`

### 2. Modify an Existing Domain Entity

✓ Domain is immutable - if you change an entity, check all dependent use cases
✓ Use value object composition
✓ Keep business logic in the entity, not in use case

```python
# In domain/audiobook_conversion/entities.py
@dataclass
class Audiobook:
    def is_complete(self) -> bool:  # Business rule logic
        return all(c.is_complete() for c in self.chapter_audiobooks)
```

### 3. Switch Infrastructure Implementation

```python
# In composition/container.py
# Simply swap one implementation for another
self._audio_processor = FFmpegAudioProcessor()  # Could be: GoogleAudioProcessor()

# No changes needed to use cases or commands!
```

### 4. Add a New External Service

1. Define protocol in domain: `domain/feature/interfaces.py`
2. Implement service in infrastructure: `infrastructure/feature/new_service.py`
3. Inject into use case via constructor
4. Register in container

```python
class NewService:
    """Implement the domain protocol"""
    def required_method(self, param: InputType) -> OutputType:
        # Implementation using external service
        ...

# Wire in container
self._new_service = NewService()
self._use_case = UseCase(self._new_service)
```

### 5. Add CLI Command

```python
# In presentation/cli/commands.py
class NewCommand:
    def __init__(self, use_case: INewUseCase) -> None:
        self._use_case = use_case

    @property
    def name(self) -> str:
        return "command-name"

    @property
    def description(self) -> str:
        return "What the command does"

    def execute(self, *args: Any, **kwargs: Any) -> str:
        # Parse kwargs, call use case, format output
        try:
            dto_input = InputDTO(**kwargs)
            dto_output = self._use_case.execute(dto_input)
            return format_output(dto_output)
        except ValueError as e:
            return f"Error: {e}"

# Register in container
container._cli_controller.register_command(NewCommand(use_case))
```

## Code Patterns

### Creating a Value Object

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable!
class MyValueObject:
    """Immutable value object."""
    id: str
    name: str

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.id.strip():
            raise ValueError("id cannot be empty")
```

### Creating an Entity

```python
from dataclasses import dataclass, field

@dataclass
class MyEntity:
    """Entity with identity and mutable state."""
    id: MyId
    name: str
    items: list[MyItem] = field(default_factory=list)

    def add_item(self, item: MyItem) -> None:
        """Business logic method."""
        if not item.is_valid():
            raise ValueError("Invalid item")
        self.items.append(item)

    def is_valid(self) -> bool:
        """Validate entity state."""
        return len(self.items) > 0
```

### Implementing a Domain Protocol

```python
from domain.feature.interfaces import MyService

class ConcreteMyService:
    """Concrete implementation of MyService protocol."""

    def required_method(self, param: str) -> str:
        """Implement the protocol method."""
        # External service call, file operation, etc.
        return result
```

### Use Case Pattern

```python
class MyUseCase:
    def __init__(self, dependency1: IService1, dependency2: IService2) -> None:
        self._dep1 = dependency1
        self._dep2 = dependency2

    def execute(self, input_dto: InputDTO) -> OutputDTO:
        """Orchestrate domain logic."""
        # Step 1: Load/validate
        entity = self._dep1.load(input_dto.id)

        # Step 2: Apply business logic
        if not entity.is_valid():
            raise ValueError("Invalid entity")
        entity.do_something()

        # Step 3: Persist
        self._dep2.save(entity)

        # Step 4: Return
        return OutputDTO(entity)
```

### DTO Pattern

```python
from dataclasses import dataclass

@dataclass
class InputDTO:
    """Input data transfer object."""
    file_path: Path
    param1: str
    param2: int = 100  # With default

    def __post_init__(self) -> None:
        if not self.file_path.exists():
            raise ValueError(f"File not found: {self.file_path}")

@dataclass
class OutputDTO:
    """Output data transfer object."""
    result: str
    count: int
```

## Key Type Hints

```python
from typing import Protocol, Any
from pathlib import Path

# Protocol for interface
class MyInterface(Protocol):
    def method(self, arg: str) -> bool: ...

# Optional returns
def get_item(id: int) -> Item | None: ...

# List/Dict types
items: list[Item] = []
mapping: dict[str, int] = {}

# Union types (multiple possibilities)
value: str | int | None

# Generic with Protocol
class Repository(Protocol):
    def find(self, id: int) -> Entity | None: ...

# Variadic args
def command(*args: Any, **kwargs: Any) -> str: ...
```

## Dependencies

```toml
# pyproject.toml
dependencies = [
    "ebooklib>=0.20",      # EPUB parsing
    "requests>=2.34.2",    # HTTP client
    "ruff>=0.16.2",        # Linter
]

# System dependencies
# - ffmpeg (for audio processing)
# - ffprobe (for audio duration detection)
```

## Running Code

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Run tests (when added)
python -m pytest

# Lint code
ruff check src/

# Format code
ruff format src/

# Check types (if using Pylance/Mypy)
pylance check src/
```

## Import Style

```python
# ✓ Correct - specific imports
from domain.feature.entities import MyEntity
from application.feature.dtos import InputDTO
from infrastructure.feature.service import ConcreteService

# ✗ Avoid - wildcard imports
from domain.feature.entities import *

# ✓ Correct - Protocol imports
from typing import Protocol

# ✗ Avoid - ABC for new code
from abc import ABC, abstractmethod
```

## Testing Patterns

```python
# Mock a service
from unittest.mock import Mock

mock_service = Mock(spec=IMyService)
mock_service.method.return_value = expected_result

# Test with mock
use_case = MyUseCase(mock_service)
result = use_case.execute(input_dto)

# Assert
assert result.expected_field == expected_value
```

## Debugging Tips

1. **Print the type**: `print(type(obj))`
2. **Check imports**: Make sure no circular dependencies
3. **Verify protocol implementation**: Match all method signatures exactly
4. **Check DTOs**: Ensure data transformation between layers
5. **Trace dependencies**: Follow constructor injection
6. **Use IDE navigation**: Ctrl+click to follow references

## Common Mistakes

❌ Putting business logic in presentation layer
✓ Keep presentation layer for formatting only

❌ Importing infrastructure in domain
✓ Domain only imports typing and built-ins

❌ Using inheritance when Protocol would work
✓ Protocols are more flexible

❌ Mixing frameworks in presentation
✓ Keep presentation framework-agnostic

❌ Circular dependencies (layer A → B → A)
✓ Always flow: Presentation → Application → Domain ← Infrastructure

## Performance Considerations

- **Text Chunking**: 45K character default, respects word boundaries
- **API Calls**: Sequential by default (can be parallelized later)
- **Audio Processing**: Happens on system via subprocess
- **File I/O**: Temporary files cleaned up after each step
- **Memory**: Chunks loaded one at a time, not all at once

## Future Enhancements

1. Parallel processing for chapters
2. Caching of generated audio chunks
3. Progress callbacks for long operations
4. Database instead of file-based storage
5. Cloud storage integration (S3, GCS)
6. Multiple audio format support
7. Volume normalization
8. Chapter markers/metadata in final MP3

## Documentation Files

- `README.md` - Project overview
- `DEVELOPMENT.md` - Development guide
- `PROJECT_STRUCTURE.md` - Detailed structure
- `ARCHITECTURE.md` - Architecture decisions
- `SCAFFOLDING_COMPLETE.md` - This scaffolding summary
- `AUDIOBOOK_IMPLEMENTATION.md` - Feature implementation details
- `FEATURE_COMPLETE.md` - Feature overview
- `CONVERSION_FLOW.md` - Detailed conversion process
- `QUICK_REFERENCE.md` - This file

## Quick Commands

```bash
# Create new feature slice
mkdir -p src/epub_converter/domain/new_feature
mkdir -p src/epub_converter/application/new_feature
mkdir -p src/epub_converter/infrastructure/new_feature

# Check for errors
pylance check src/

# Run type checker
mypy src/

# Format with ruff
ruff format src/

# Check with ruff
ruff check --fix src/
```

## Support

For questions about:

- **Architecture**: See `ARCHITECTURE.md`
- **Implementation**: See `AUDIOBOOK_IMPLEMENTATION.md`
- **Conversion Flow**: See `CONVERSION_FLOW.md`
- **Development**: See `DEVELOPMENT.md`
