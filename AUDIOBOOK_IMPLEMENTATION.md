# EPUB to Audiobook Converter - Implementation Guide

This document describes the implementation of the audiobook conversion feature following clean architecture principles with strict typing.

## Architecture Overview

The audiobook conversion feature is implemented across all layers of the clean architecture:

### Domain Layer (`domain/audiobook_conversion/`)

Contains purely business logic with no dependencies on other layers.

**Value Objects** (`value_objects.py`):

- `AudioProfile`: Represents a voice profile from VoiceBox
- `AudioProfileId`: Unique identifier for voice profiles
- `TextChunk`: A chunk of text (max 45K chars) to be converted to speech
- `AudioFile`: A generated MP3 file from a text chunk

**Entities** (`entities.py`):

- `ChapterAudiobook`: Audio version of a single chapter (multiple audio file chunks)
- `Audiobook`: Aggregate root representing the complete audiobook

**Interfaces/Protocols** (`interfaces.py`):

- `VoiceBoxService`: Contract for VoiceBox API interactions
- `TextChunker`: Contract for text chunking strategy
- `AudioProcessor`: Contract for audio file operations (merge, duration)
- `AudiobookRepository`: Contract for audiobook persistence

### Application Layer (`application/audiobook_conversion/`)

Orchestrates domain logic and defines use cases.

**DTOs** (`dtos.py`):

- `ConvertEPUBToAudiobookInput`: Input parameters for conversion
- `ConvertEPUBToAudiobookOutput`: Result of conversion with metadata
- `ListVoiceProfilesOutput`: Available voice profiles

**Interfaces/Protocols** (`interfaces.py`):

- `IConvertEPUBToAudiobookUseCase`: Protocol for conversion use case
- `IListVoiceProfilesUseCase`: Protocol for listing profiles

**Use Cases** (`use_cases.py`):

- `ConvertEPUBToAudiobookUseCase`: Orchestrates the full conversion workflow
- `ListVoiceProfilesUseCase`: Retrieves available voice profiles

### Infrastructure Layer (`infrastructure/audiobook_conversion/`)

Concrete implementations of domain interfaces.

**VoiceBox Service** (`voicebox_service.py`):

- `VoiceBoxApiService`: Communicates with VoiceBox REST API
- `TextChunkerService`: Splits text at word boundaries to stay within size limits

**Audio Processing** (`audio_processor.py`):

- `FFmpegAudioProcessor`: Uses FFmpeg for audio file operations

**Repository** (`repository.py`):

- `AudiobookFileRepository`: Stores audiobooks and metadata in the filesystem

### Presentation Layer (`presentation/cli/audiobook_conversion_commands.py`)

Framework-agnostic CLI command definitions.

- `ConvertEPUBToAudiobookCommand`: Command for converting EPUB to audiobook
- `ListVoiceProfilesCommand`: Command for listing available voices

### Composition Root (`composition/container.py`)

Wires all dependencies together for dependency injection.

## Conversion Workflow

```
EPUB File
    ↓
Load EPUB (via EPUBRepository)
    ↓
For Each Chapter:
    ├─ Chunk Text (TextChunkerService, 45K chars max)
    │   └─ For Each Chunk:
    │       └─ Generate Speech (VoiceBoxApiService)
    │           └─ Save chunk MP3
    ├─ Merge Chunk Audio Files (FFmpegAudioProcessor)
    └─ Delete chunk files
    ↓
Merge All Chapter Audio Files (FFmpegAudioProcessor)
    ↓
Save Audiobook Metadata (AudiobookFileRepository)
    ↓
Output MP3 File
```

## Usage Examples

### Convert EPUB to Audiobook

```python
from pathlib import Path
from epub_converter.composition.container import Container

# Initialize container with default VoiceBox API
container = Container()

# Or with custom VoiceBox URL
container = Container(voicebox_url="http://custom-voicebox:17493")

# Get the use case
use_case = container.convert_audiobook_use_case

# Prepare input
from epub_converter.application.audiobook_conversion.dtos import ConvertEPUBToAudiobookInput

input_dto = ConvertEPUBToAudiobookInput(
    epub_file_path=Path("book.epub"),
    output_file_path=Path("book_audiobook.mp3"),
    voice_profile_id="abc123",  # From list-voice-profiles command
    language="en",
    chunk_size=45000
)

# Execute conversion
output_dto = use_case.execute(input_dto)
print(f"Audiobook saved to: {output_dto.output_file_path}")
print(f"Duration: {output_dto.total_duration_seconds} seconds")
print(f"Chapters: {output_dto.chapter_count}")
```

### List Available Voice Profiles

```python
from epub_converter.composition.container import Container

container = Container()
use_case = container._list_voices_use_case

output_dto = use_case.execute()
for profile in output_dto.profiles:
    print(f"{profile['id']}: {profile['name']} ({profile['language']})")
    print(f"  {profile['description']}")
```

### Via CLI Commands

```bash
# List available voice profiles
epub-converter list-voices

# Convert EPUB to audiobook
epub-converter convert-to-audiobook /path/to/book.epub \
  --output /path/to/book_audiobook.mp3 \
  --profile abc123 \
  --language en \
  --chunk-size 45000

# Convert a directory of chapter .txt files (e.g. from extract-chapters) to audiobook
epub-converter convert-to-audiobook --text-dir /path/to/chapters/ \
  --output /path/to/book_audiobook.mp3 \
  --profile abc123
```

## Dependencies

### External Services

- **VoiceBox**: REST API service at `http://127.0.0.1:17493`
  - Endpoint: `GET /profiles` - List available voice profiles
  - Endpoint: `POST /generate` - Enqueue speech generation from text; returns a
    `GenerationResponse` with an `id` and an in-progress `status`
    (`queued`, `loading_model`, `generating`, ...)
  - Endpoint: `GET /generate/{id}/status` - Server-sent-events stream of
    status snapshots; polled until a terminal status (`completed`,
    `failed`, `error`, `cancelled`) is reached
  - Endpoint: `GET /history/{id}/export-audio` - Download the finished MP3
    once the generation has completed

### System Requirements

- **FFmpeg**: Required for audio file merging and duration detection
  - Install: `apt-get install ffmpeg` (Linux) or `brew install ffmpeg` (macOS)
  - Windows: Download from https://ffmpeg.org/download.html

### Python Dependencies

- `requests>=2.34.2`: For HTTP calls to VoiceBox
- `ebooklib>=0.20`: For reading EPUB files

## Error Handling

### VoiceBox Connection Errors

```python
RuntimeError: Failed to retrieve voice profiles: [Connection error details]
```

**Solution**: Ensure VoiceBox service is running at the configured URL.

### FFmpeg Not Found

```python
RuntimeError: ffmpeg is not installed or not in PATH.
```

**Solution**: Install FFmpeg and ensure it's in your system PATH.

### Invalid Input

```python
ValueError: EPUB file not found: /path/to/nonexistent.epub
```

**Solution**: Verify the EPUB file path exists.

### Audio Generation Failure

```python
RuntimeError: Failed to generate speech: [API error details]
```

**Solution**:

- Check voice profile ID is valid (use `list-voice-profiles`)
- Verify text is not empty
- Check VoiceBox service logs

## Configuration

### VoiceBox Service URL

Pass custom URL when creating the container:

```python
container = Container(voicebox_url="http://voicebox-server:17493")
```

Or set environment variable (when CLI framework is updated):

```bash
export VOICEBOX_URL="http://voicebox-server:17493"
```

### Text Chunk Size

Default is 45,000 characters. Adjust based on VoiceBox API limits:

```python
input_dto = ConvertEPUBToAudiobookInput(
    ...,
    chunk_size=30000  # Smaller chunks for slower systems
)
```

## Testing Considerations

### Mocking VoiceBox Service

```python
class MockVoiceBoxService:
    def get_available_profiles(self):
        return [
            AudioProfile(
                id=AudioProfileId("mock1"),
                name="Mock Voice",
                language="en",
                description="Test profile"
            )
        ]

    def generate_speech(self, text, profile_id, language):
        # Return minimal MP3 data for testing
        return b"ID3" + b"\x00" * 100  # Fake MP3 header
```

### Extending the System

To add support for a new voice service (e.g., Google Cloud TTS):

1. Create a new domain interface in `domain/audiobook_conversion/interfaces.py`
2. Create an infrastructure implementation in `infrastructure/`
3. Update `Container` to support both services
4. No changes needed to domain logic or use cases

This design makes it easy to swap implementations without affecting business logic.

## Performance Notes

- Text chunking respects word boundaries to avoid cutting mid-word
- Audio files are processed sequentially per chapter to manage memory
- Temporary chunk files are cleaned up after merging
- Total audiobook duration is calculated from FFmpeg

## Future Enhancements

1. **Parallel Processing**: Process multiple chapters concurrently
2. **Caching**: Cache generated audio for identical text chunks
3. **Progress Tracking**: Implement progress callbacks for long conversions
4. **Audio Normalization**: Normalize volume levels across chunks
5. **Format Support**: Add support for other audio formats (AAC, OGG)
6. **Database Storage**: Replace file-based repository with proper database
7. **Cloud Integration**: Support remote audio storage (S3, GCS)
