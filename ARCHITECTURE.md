"""Architecture documentation for epub-converter.

This project follows Clean Architecture principles with strict typing throughout.
"""

# ARCHITECTURE OVERVIEW

## Layers

### 1. Domain Layer (`domain/`)

The core business logic and entities with **zero external dependencies**.

**Contains:**

- Entities: Aggregate roots like `EPUBFile`, `Chapter`
- Value Objects: Immutable objects like `FilePath`, `Metadata`, `ChapterId`
- Interfaces: Abstract contracts for repositories (e.g., `EPUBRepository`)

**Key Principle:** No knowledge of databases, frameworks, or I/O. Only pure business logic.

### 2. Application Layer (`application/`)

Use cases that orchestrate domain logic and handle application-specific workflows.

**Depends on:** Domain layer only

**Contains:**

- Use Cases: Orchestrate domain entities (e.g., `LoadEPUBUseCase`, `ExtractChapterUseCase`)
- DTOs: Data transfer objects for input/output (e.g., `LoadEPUBInput`, `LoadEPUBOutput`)
- Interfaces: Define contracts for infrastructure implementations

**Key Principle:** Expresses business rules in terms of use cases. No framework dependencies.

### 3. Presentation Layer (`presentation/`)

CLI commands and output formatting. Framework-agnostic command definitions.

**Depends on:** Application layer

**Contains:**

- Commands: Abstract command definitions (e.g., `LoadEPUBCommand`)
- Controller: Routes commands and orchestrates CLI interaction
- Responses: Formatting utilities for user output

**Key Principle:** No dependency on specific CLI frameworks. Easy to swap between Click, Typer, or custom CLI.

### 4. Infrastructure Layer (`infrastructure/`)

Concrete implementations of domain and application interfaces.

**Depends on:** Domain and Application layers

**Contains:**

- Repositories: Concrete file I/O implementations (e.g., `EbookLibEPUBRepository`)
- Services: External service integrations
- Framework-specific code

**Key Principle:** All external dependencies live here. Easy to swap implementations.

### 5. Composition Root (`composition/`)

Wires up dependencies and configures the application.

**Contains:**

- Container: Dependency injection container
- Factory methods: Creates fully configured objects

**Key Principle:** Single location for dependency configuration.

---

## Vertical Feature Slices

Within each layer, features are organized using **vertical slices** rather than layers within layers.

### Example: EPUB Extraction Feature

```
domain/epub_extraction/          # Domain logic for this feature
├── entities.py
├── value_objects.py
└── interfaces.py

application/epub_extraction/     # Use cases for this feature
├── dtos.py
├── use_cases.py
└── interfaces.py

infrastructure/epub_extraction/  # Infrastructure for this feature
└── repositories.py

presentation/cli/
└── epub_extraction_commands.py  # CLI commands for this feature
```

This organization makes it easy to:

- Find all code related to EPUB extraction
- Understand feature boundaries
- Add new features without modifying existing ones
- Test features in isolation

---

## Dependency Flow

```
Composition Root
       ↓
Presentation Layer (CLI Commands)
       ↓
Application Layer (Use Cases)
       ↓
Domain Layer (Entities, Value Objects)

Infrastructure Layer (Implementations)
       ↓
    (Injected into Application & Domain)
```

**Key Rule:** Dependencies point inward. Never upward.

---

## Adding a New Feature

To add a new feature (e.g., format conversion):

1. **Domain** (`domain/format_conversion/`):
   - Define entities and value objects
   - Define repository interfaces

2. **Application** (`application/format_conversion/`):
   - Create use cases
   - Define DTOs
   - Create application interfaces

3. **Infrastructure** (`infrastructure/format_conversion/`):
   - Implement domain repository interfaces
   - Implement external service integrations

4. **Presentation** (`presentation/cli/`):
   - Create CLI commands
   - Define command options and output formatting

5. **Composition** (`composition/container.py`):
   - Wire dependencies
   - Register commands

---

## Strict Typing

All code uses Python type hints for:

- Function arguments and return types
- Class attributes
- Module-level functions

**Example:**

```python
def execute(self, input_dto: LoadEPUBInput) -> LoadEPUBOutput:
    """Execute the use case."""
```

Use `mypy` or `pyright` to validate types:

```bash
mypy src/epub_converter
```

---

## Testing Strategy

### Unit Tests

- Test entities and value objects in isolation
- Test use cases with mock repositories

### Integration Tests

- Test repository implementations with real files
- Test full command execution flow

### Example Structure:

```
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   └── presentation/
├── integration/
│   └── infrastructure/
└── e2e/
    └── cli/
```

---

## Key Design Decisions

1. **Immutable Value Objects**: Prevent accidental state changes
2. **Explicit Interfaces**: Clear contracts for dependency injection
3. **DTOs for Layer Boundaries**: Prevent leaking internal representations
4. **Framework Agnostic**: Presentation layer can be replaced with web API
5. **Feature-Based Organization**: Easier to reason about and modify features
