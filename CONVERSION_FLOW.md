# Audiobook Conversion - Detailed Flow Diagram

## High-Level Conversion Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI User Input                             │
├─────────────────────────────────────────────────────────────────┤
│  epub_file: /path/to/book.epub                                 │
│  output_file: /path/to/book_audiobook.mp3                      │
│  voice_profile_id: "voice_abc123"                               │
│  language: "en"                                                  │
│  chunk_size: 45000                                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────────────┐
        │ ConvertEPUBToAudiobookCommand   │
        │ (Presentation Layer)             │
        └──────────────────┬───────────────┘
                           │
                           ↓
        ┌───────────────────────────────────────────┐
        │ ConvertEPUBToAudiobookUseCase.execute()  │
        │ (Application Layer)                       │
        │                                           │
        │ Input: ConvertEPUBToAudiobookInput      │
        └───────────────────┬───────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ↓                                   ↓
    ┌──────────────────┐            ┌────────────────────┐
    │ Load EPUB File   │            │ Prepare Output Dir │
    │ (Step 1)         │            │                    │
    └────────┬─────────┘            └────────────────────┘
             │
             ↓
    ┌────────────────────────────────────────┐
    │ EPUBRepository.load()                  │
    │ (via EbookLibEPUBRepository)           │
    │ Returns: EPUBFile entity with chapters │
    └────────┬───────────────────────────────┘
             │
             ├─────────────────┐
             │                 │
             ↓                 ↓
    Chapter 1: "Ch 1"  Chapter 2: "Ch 2" ...
             │                 │
             ↓                 ↓
    ┌──────────────────────────────────┐
    │ For Each Chapter:                 │
    │ (Step 2-4)                        │
    ├──────────────────────────────────┤
    │ 2. Chunk Text                    │
    │    TextChunkerService.chunk_text()│
    │    Splits at word boundaries      │
    │    Max 45K chars per chunk        │
    │                                  │
    │ Input: Chapter text              │
    │ Output: [TextChunk(...), ...]   │
    │                                  │
    │ 3. Generate Speech per Chunk     │
    │    For each TextChunk:           │
    │    - VoiceBoxApiService          │
    │      .generate_speech()          │
    │    - Returns: MP3 bytes          │
    │    - Save: chunk_0.mp3,          │
    │      chunk_1.mp3, ...            │
    │                                  │
    │ 4. Merge Chunk Audio Files       │
    │    FFmpegAudioProcessor          │
    │    .merge_audio_files()          │
    │    Input: [chunk_0.mp3, ...]    │
    │    Output: chapter_1.mp3         │
    │    Delete temporary files        │
    └────────┬───────────────────────────┘
             │
             │ Repeat for each chapter
             ↓
    ┌──────────────────────────────────┐
    │ Merge All Chapter Audio Files    │
    │ (Step 5)                          │
    │                                  │
    │ FFmpegAudioProcessor             │
    │ .merge_audio_files()             │
    │ Input: [chapter_1.mp3,           │
    │         chapter_2.mp3, ...]      │
    │ Output: final_audiobook.mp3      │
    └────────┬───────────────────────────┘
             │
             │ Delete chapter files
             ↓
    ┌──────────────────────────────────┐
    │ Save Audiobook Metadata          │
    │ (Step 6)                          │
    │                                  │
    │ AudiobookRepository              │
    │ .save_audiobook()                │
    │ Saves JSON metadata              │
    └────────┬───────────────────────────┘
             │
             ↓
    ┌──────────────────────────────────┐
    │ Get Audio Duration               │
    │ (Step 7)                          │
    │                                  │
    │ FFmpegAudioProcessor             │
    │ .get_audio_duration()            │
    │ Uses ffprobe                     │
    └────────┬───────────────────────────┘
             │
             ↓
    ┌──────────────────────────────────┐
    │ Return Output DTO                │
    │ (Application Layer)              │
    │                                  │
    │ ConvertEPUBToAudiobookOutput    │
    │ - output_file_path               │
    │ - total_duration_seconds         │
    │ - chapter_count                  │
    │ - voice_profile_id               │
    └────────┬───────────────────────────┘
             │
             ↓
    ┌──────────────────────────────────┐
    │ Format Output                    │
    │ (Presentation Layer)             │
    │                                  │
    │ ConvertEPUBToAudiobookCommand   │
    │ .execute()                       │
    │ Returns formatted string         │
    └────────┬───────────────────────────┘
             │
             ↓
    ┌──────────────────────────────────┐
    │ Display to User                  │
    │                                  │
    │ "Successfully converted..."      │
    │ "Output: /path/book_audiobook.mp3"
    │ "Duration: 12345.5 seconds"      │
    │ "Chapters: 15"                   │
    │ "Voice Profile: voice_abc123"   │
    └──────────────────────────────────┘
```

## Detailed Service Interaction Sequence

```
Sequence: EPUB to Audiobook Conversion

┌────────────────────────────────────────────────────────────────────┐
│                           Time                                     │
├────────────────────────────────────────────────────────────────────┤
│
│ [0] User → CLI Command
│     └─→ ParseInput(epub_file, output_file, voice_id, language)
│
│ [1] ConvertEPUBToAudiobookCommand
│     └─→ ConvertEPUBToAudiobookUseCase.execute()
│
│ [2] ConvertEPUBToAudiobookUseCase
│     └─→ EPUBRepository.load(FilePath)
│
│ [3] EbookLibEPUBRepository
│     └─→ zipfile.ZipFile
│     └─→ ebooklib.epub.read_epub()
│     └─→ Extract chapters, metadata
│     └─→ Return EPUBFile(chapters=[...])
│
│ [4] ConvertEPUBToAudiobookUseCase
│     └─→ For each chapter:
│
│ [5]     TextChunkerService.chunk_text(chapter.content, 45000)
│         └─→ Split at word boundaries
│         └─→ Return [TextChunk(sequence=0, text="...", ...),
│                      TextChunk(sequence=1, text="...", ...),
│                      ...]
│
│ [6]     For each chunk:
│         └─→ VoiceBoxApiService.generate_speech(
│                 text=chunk.text,
│                 profile_id="voice_abc123",
│                 language="en"
│             )
│
│ [7]         requests.post(
│                 "http://127.0.0.1:17493/generate",
│                 json={
│                     "text": chunk.text,
│                     "profile_id": "voice_abc123",
│                     "language": "en"
│                 }
│             )
│             └─→ Returns GenerationResponse{id, status="generating", ...}
│                 immediately (generation runs asynchronously)
│
│ [8]         GET /generate/{id}/status (server-sent-events stream)
│             └─→ Watch status snapshots: queued -> loading_model ->
│                 generating -> completed (or failed/error/cancelled)
│             └─→ Reopen the stream on transient drops until a terminal
│                 status arrives or the timeout elapses
│
│ [9]         GET /history/{id}/export-audio
│             └─→ Return: bytes (MP3 data)
│             └─→ Save to chunk_0.mp3
│
│ [10]        Repeat for all chunks of chapter
│
│ [11]    FFmpegAudioProcessor.merge_audio_files(
│             [chunk_0.mp3, chunk_1.mp3, ...],
│             chapter_1.mp3
│         )
│
│ [12]        Create concat demuxer file:
│             file 'chunk_0.mp3'
│             file 'chunk_1.mp3'
│             ...
│
│ [13]        subprocess.run([
│                 "ffmpeg",
│                 "-f", "concat",
│                 "-safe", "0",
│                 "-i", "concat.txt",
│                 "-c", "copy",
│                 "-y",
│                 "chapter_1.mp3"
│             ])
│
│ [14]        FFmpeg merges files
│             └─→ Copies codec streams
│             └─→ Produces chapter_1.mp3
│
│ [15]        Delete chunk files
│
│ [16]    Repeat for all chapters
│
│ [17]    FFmpegAudioProcessor.merge_audio_files(
│             [chapter_1.mp3, chapter_2.mp3, ...],
│             final_audiobook.mp3
│         )
│
│ [18]        Create concat file
│             └─→ Run ffmpeg
│             └─→ Produce final_audiobook.mp3
│
│ [19]        Delete chapter files
│
│ [20]    AudiobookRepository.save_audiobook(audiobook_obj)
│         └─→ Create metadata JSON
│         └─→ Save to ~/.epub-converter/audiobooks/.metadata/
│
│ [21]    FFmpegAudioProcessor.get_audio_duration(final_audiobook.mp3)
│
│ [22]        subprocess.run([
│                 "ffprobe",
│                 "-v", "error",
│                 "-show_entries", "format=duration",
│                 "final_audiobook.mp3"
│             ])
│
│ [23]        ffprobe outputs duration
│             └─→ Return: 12345.5 (seconds)
│
│ [24]    ConvertEPUBToAudiobookOutput(
│             output_file_path=Path("final_audiobook.mp3"),
│             total_duration_seconds=12345.5,
│             chapter_count=15,
│             voice_profile_id="voice_abc123"
│         )
│
│ [25]    ConvertEPUBToAudiobookCommand.execute()
│         └─→ Format output message
│         └─→ Return formatted string
│
│ [26]    Display to user
│         "Successfully converted EPUB to audiobook
│          Output: /path/to/final_audiobook.mp3
│          Duration: 12345.5 seconds
│          Chapters: 15
│          Voice Profile: voice_abc123"
│
└────────────────────────────────────────────────────────────────────┘
```

## File Operations Timeline

```
Before: /path/to/input.epub

After: /path/to/input_audiobook.mp3
       + ~/.epub-converter/audiobooks/.metadata/input_audiobook.json

Temporary files (created and deleted):
  Intermediate files (deleted after use):
    - chapter_0_chunk_0.mp3
    - chapter_0_chunk_1.mp3
    - ...
    - chapter_0.mp3 (merged chunks, then deleted)
    - chapter_1_chunk_0.mp3
    - ...
    - chapter_1.mp3 (merged chunks, then deleted)
    ...

Final output:
    - input_audiobook.mp3 (final merged audiobook)
    - ~/.epub-converter/audiobooks/.metadata/input_audiobook.json (metadata)
```

## Error Handling Paths

```
ConvertEPUBToAudiobookCommand.execute()
├─ ValueError: Invalid Input
│  ├─ EPUB file not found
│  ├─ Invalid chunk size
│  └─ Missing voice profile ID
│
└─ RuntimeError: Conversion Failed
   ├─ EPUB Loading Failed
   │  └─ Invalid EPUB format
   │
   ├─ Text Chunking Failed
   │  └─ Empty text
   │
   ├─ Speech Generation Failed
   │  ├─ VoiceBox not accessible
   │  │  └─ Connection refused
   │  ├─ Invalid profile ID
   │  └─ API error response
   │
   ├─ Audio Processing Failed
   │  ├─ FFmpeg not found
   │  ├─ ffprobe not found
   │  └─ Audio merge failed
   │
   └─ Metadata Save Failed
      └─ File system error
```

## Memory and Performance Characteristics

```
Memory Usage:
- EPUB file: O(n) where n = file size
- All chapters: O(total_chapters * avg_chapter_size)
- Chunks in memory: O(chunk_size) (45KB default)
- Audio data in memory: O(chunk_size_bytes) temporary
- Final MP3: O(audio_duration_bytes)

Time Complexity:
- EPUB parsing: O(n) where n = file size
- Text chunking: O(n) where n = total text length
- API calls: O(chunks) sequential (not parallel)
- Audio merging: O(chapters) per chapter merge + O(chapters) final merge
- Total: O(total_text_length + chapters)

I/O Operations:
- 1 Read: EPUB file
- N_chunks Writes: Temporary chunk audio files
- 1 Read per chunk: FFmpeg processes chunk files
- N_chapters Writes: Chapter audio files
- 1 Read per chapter: FFmpeg processes chapter files
- 1 Write: Final audiobook file
- 1 Write: Metadata JSON file
```

## Extensibility Points

The architecture allows easy extension:

```
1. New Voice Services:
   - Implement VoiceBoxService protocol
   - Add to Container
   - No use case changes needed

2. New Audio Formats:
   - Extend FFmpegAudioProcessor
   - Support new file extensions
   - Use case doesn't care about format

3. New Chunking Strategies:
   - Implement TextChunker protocol
   - Add to Container
   - Swap implementations easily

4. New Persistence:
   - Implement AudiobookRepository protocol
   - Database, cloud storage, etc.
   - Use case doesn't care about storage

5. New CLI Frameworks:
   - Commands already framework-agnostic
   - Adapt controller to Click, Typer, etc.
   - No domain/application changes needed
```

## Testing Strategy

```
Unit Tests (No External Dependencies):
├─ Domain Layer
│  ├─ Entity validation
│  ├─ Value object immutability
│  └─ Aggregate invariants
│
└─ Application Layer
   ├─ Use case orchestration logic
   └─ DTO transformations

Integration Tests (With Mocked Services):
├─ Use case workflows
├─ Service interactions
└─ Error handling paths

End-to-End Tests (Full Stack):
├─ Real EPUB files
├─ Mock VoiceBox service
├─ Real FFmpeg
└─ File system operations
```
