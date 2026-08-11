# Audiobook Conversion Feature - Complete Project Structure

## Updated Project Structure

```
src/epub_converter/
├── domain/
│   ├── audiobook_conversion/              [NEW]
│   │   ├── __init__.py
│   │   ├── entities.py                 # Audiobook, ChapterAudiobook
│   │   ├── value_objects.py            # AudioProfile, TextChunk, AudioFile
│   │   └── interfaces.py               # VoiceBoxService, TextChunker, AudioProcessor, AudiobookRepository
│   │
│   └── epub_extraction/
│       ├── __init__.py
│       ├── entities.py
│       ├── value_objects.py
│       └── interfaces.py
│
├── application/
│   ├── audiobook_conversion/              [NEW]
│   │   ├── __init__.py
│   │   ├── dtos.py                     # ConvertEPUBToAudiobookInput/Output, ListVoiceProfilesOutput
│   │   ├── interfaces.py               # IConvertEPUBToAudiobookUseCase, IListVoiceProfilesUseCase
│   │   └── use_cases.py                # ConvertEPUBToAudiobookUseCase, ListVoiceProfilesUseCase
│   │
│   └── epub_extraction/
│       ├── __init__.py
│       ├── dtos.py
│       ├── interfaces.py
│       └── use_cases.py
│
├── infrastructure/
│   ├── audiobook_conversion/              [NEW]
│   │   ├── __init__.py
│   │   ├── voicebox_service.py         # VoiceBoxApiService, TextChunkerService
│   │   ├── audio_processor.py          # FFmpegAudioProcessor
│   │   └── repository.py               # AudiobookFileRepository
│   │
│   └── epub_extraction/
│       ├── __init__.py
│       └── repositories.py
│
├── presentation/
│   └── cli/
│       ├── __init__.py
│       ├── commands.py                 # Base Command protocol
│       ├── controller.py
│       ├── responses.py
│       ├── epub_extraction_commands.py
│       └── audiobook_conversion_commands.py   [NEW]
│           ├── ConvertEPUBToAudiobookCommand
│           └── ListVoiceProfilesCommand
│
└── composition/
    └── container.py                        [UPDATED]
        # Wires all dependencies for both EPUB extraction and audiobook conversion
```

## Feature: Extract EPUB to Chapters with Text

**Use Case**: `ExtractChapterUseCase`

- Input: EPUB file path
- Process: Load EPUB, extract chapters, get raw text content
- Output: List of chapters with metadata and text

**CLI Command**: `extract-epub` (existing)

## Feature: Convert EPUB to Audiobook

**Primary Use Case**: `ConvertEPUBToAudiobookUseCase`

**Process Flow**:

1. Load EPUB file via `EPUBRepository`
2. For each chapter:
   - Chunk text into 45K character segments using `TextChunker`
   - For each chunk:
     - Call `VoiceBoxService.generate_speech()` to get audio
     - Save temporary chunk MP3 file
   - Merge all chunk audio files into chapter audio using `AudioProcessor`
   - Clean up temporary chunk files
3. Merge all chapter audio files into final audiobook
4. Save audiobook metadata via `AudiobookRepository`
5. Return conversion result with duration and metadata

**Secondary Use Case**: `ListVoiceProfilesUseCase`

- Retrieves available voice profiles from VoiceBox API
- Used to display available options to users

**CLI Commands**:

- `list-voice-profiles`: Display available voice profiles
- `convert-epub-to-audiobook`: Convert EPUB to MP3 audiobook

## Integration Points

### VoiceBox API Integration

- **Service**: `VoiceBoxApiService`
- **Endpoint 1**: `GET http://127.0.0.1:17493/profiles`
  - Returns: List of voice profiles with id, name, language, description
- **Endpoint 2**: `POST http://127.0.0.1:17493/generate`
  - Input: `{"text": "...", "profile_id": "...", "language": "en"}`
  - Returns: MP3 audio data (binary or base64-encoded JSON)

### FFmpeg Integration

- **Service**: `FFmpegAudioProcessor`
- **Commands Used**:
  - `ffmpeg -f concat -safe 0 -i concat_file.txt -c copy output.mp3`
  - `ffprobe -v error -show_entries format=duration ...`
- **Purpose**: Merge multiple MP3 files into single output

### Dependency Injection

- **Container**: `epub_converter.composition.container.Container`
- **Wiring**: All services, use cases, and commands initialized with proper dependencies
- **CLI Integration**: All commands registered with CLI controller

## Clean Architecture Compliance

### Dependency Flow

```
CLI Commands (Presentation)
    ↓ (depends on)
Use Cases (Application)
    ↓ (depends on)
Domain Interfaces/Protocols
    ↓ (implemented by)
Infrastructure Services
```

### No Circular Dependencies

- Domain layer: Zero dependencies ✓
- Application layer: Depends only on domain ✓
- Infrastructure: No business logic, implements domain contracts ✓
- Presentation: Depends on application layer ✓

### Strict Typing

- All functions have type hints ✓
- Protocols used instead of ABC ✓
- Value objects immutable with frozen dataclasses ✓
- DTOs for layer boundaries ✓

## Testing Strategy

### Unit Testing

- Domain entities and value objects (no external dependencies)
- Use case orchestration logic (with mocked services)

### Integration Testing

- VoiceBox API integration (with test server or mocks)
- FFmpeg audio processing (with sample MP3 files)
- File system operations (with temp directories)

### Example Mock Setup

```python
class MockVoiceBoxService:
    def get_available_profiles(self) -> list[AudioProfile]:
        return [AudioProfile(...)]

    def generate_speech(self, text, profile_id, language) -> bytes:
        return b"ID3" + b"\x00" * 1000  # Minimal MP3

class MockAudioProcessor:
    def get_audio_duration(self, audio_file):
        return 120.5

    def merge_audio_files(self, files, output):
        output.write_bytes(b"ID3" + b"\x00" * 1000)
```

## Next Steps

1. **Configuration Management**: Add config file for VoiceBox URL, chunk size, output directory
2. **CLI Framework Integration**: Connect to Click, Typer, or similar CLI framework
3. **Error Recovery**: Add retry logic for failed API calls
4. **Progress Reporting**: Add callbacks for long-running conversions
5. **Testing**: Add comprehensive test suite
6. **Documentation**: Create user guide for running the converter
