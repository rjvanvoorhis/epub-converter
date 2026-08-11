# EPUB Converter - Project Structure

```
epub-converter/
├── pyproject.toml                          # Project configuration
├── README.md                               # Project README
├── ARCHITECTURE.md                         # Architecture documentation
├── DEVELOPMENT.md                          # Development guide
│
└── src/epub_converter/
    ├── __init__.py                         # CLI entry point (main)
    │
    ├── domain/                             # ─────────────────────────────────────
    │   ├── __init__.py                     # Domain layer - Pure business logic
    │   └── epub_extraction/                # (no external dependencies)
    │       ├── __init__.py                 #
    │       ├── entities.py                 # Entities: EPUBFile, Chapter
    │       ├── value_objects.py            # Value Objects: FilePath, Metadata
    │       └── interfaces.py               # Interfaces: EPUBRepository
    │
    ├── application/                        # ─────────────────────────────────────
    │   ├── __init__.py                     # Application layer - Use cases
    │   └── epub_extraction/                # (depends only on domain)
    │       ├── __init__.py                 #
    │       ├── dtos.py                     # DTOs: LoadEPUBInput/Output, etc.
    │       ├── use_cases.py                # Use Cases: LoadEPUBUseCase, etc.
    │       └── interfaces.py               # Interfaces: ILoadEPUBUseCase, etc.
    │
    ├── presentation/                       # ─────────────────────────────────────
    │   ├── __init__.py                     # Presentation layer - CLI framework-agnostic
    │   └── cli/                            # (depends on application layer)
    │       ├── __init__.py                 #
    │       ├── commands.py                 # Base Command class (abstract)
    │       ├── epub_extraction_commands.py # Feature commands: LoadEPUBCommand, etc.
    │       ├── controller.py               # CLIController - routes commands
    │       └── responses.py                # Response formatting utilities
    │
    ├── infrastructure/                     # ─────────────────────────────────────
    │   ├── __init__.py                     # Infrastructure layer - Concrete impl.
    │   └── epub_extraction/                # (all external dependencies here)
    │       ├── __init__.py                 #
    │       └── repositories.py             # Concrete: EbookLibEPUBRepository
    │
    └── composition/                        # ─────────────────────────────────────
        ├── __init__.py                     # Composition root - Dependency injection
        └── container.py                    # Container class - wires dependencies
```

## Key Concepts

### Vertical Feature Slices

Each feature (like `epub_extraction`) is organized vertically across all layers:

```
Feature: EPUB Extraction
├── domain/epub_extraction/       ← Business logic
├── application/epub_extraction/  ← Use cases
├── infrastructure/epub_extraction/ ← Implementations
└── presentation/cli/
    └── epub_extraction_commands.py ← CLI commands
```

### Dependency Flow

```
CLI Entry Point
    ↓
Composition Root (Container)
    ↓
Presentation Layer (Commands) → Application Layer (Use Cases)
                                    ↓
                              Domain Layer (Entities)
                                    ↑
Infrastructure Layer (Repositories) ← Injected into Application
```

**Rule:** Dependencies flow inward. Never upward.

### Layer Responsibilities

| Layer              | Purpose                                   | Dependencies        |
| ------------------ | ----------------------------------------- | ------------------- |
| **Domain**         | Pure business logic, entities, aggregates | None                |
| **Application**    | Use cases orchestrating domain            | Domain only         |
| **Presentation**   | CLI commands, user interaction            | Application         |
| **Infrastructure** | File I/O, external libraries              | Domain, Application |
| **Composition**    | Wires everything together                 | All layers          |

## Important Files

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture explanation and design decisions
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Setup, testing, and development workflow
- **[src/epub_converter/**init**.py](src/epub_converter/__init__.py)** - CLI entry point

## Next Steps

1. **Add Tests**: Create test files following the structure in DEVELOPMENT.md
2. **Add More Features**: Follow the vertical slice pattern to add new features
3. **Implement CLI Framework**: Integrate with Click, Typer, or argparse if desired
4. **Add Configuration**: Create config files and environment handling
