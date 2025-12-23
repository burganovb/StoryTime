# StoryTime

MVP for a kid-friendly story-to-comic web app (mobile-first, optimized for iPad/iPhone Safari).

## Goals (MVP)
- **One tap to record** 10–60 seconds of narration.
- **Generate 4–8 comic panels** (MVP: 4 panels) progressively.
- **Save and replay** stories later.
- **No sharing, no payments, no accounts** (optional parent passcode gate).

## Architecture
### Client
- **Web app** (mobile-first).
- **Targets**: iPad Safari, iPhone Safari.
- **Core screens**: Home, Record, Generate, Story Viewer, My Stories.

### Backend
- **FastAPI** (Python).
- **DB**: SQLite for prototype, Postgres (Supabase) for production.
- **Storage**: S3-compatible (e.g., Supabase Storage).
- **AI Components**
  - **Speech-to-text**: Whisper (or Deepgram for speed).
  - **Story beat generator**: LLM transforms transcript → structured panel prompts.
  - **Image generation**: single model, single style for consistent output.

## Vertical Slice (Phase 1)
### Slice A: Record → Transcript → Generate 4 Panels
1. Record audio (10–60s).
2. Run STT to generate transcript.
3. Generate exactly **4 panels**:
   - **Panel 1**: Setting + hero
   - **Panel 2**: Problem
   - **Panel 3**: Action
   - **Panel 4**: Outcome

### Slice B: Save and View
1. Persist story (title, transcript, audio URL, panel URLs).
2. Show in **My Stories** list.
3. Story viewer loads instantly and supports swipe.

## Data Model (Minimal)
```json
Story {
  id: string,
  title: string,
  created_at: datetime,
  audio_url: string,
  transcript: string,
  panels: [
    { image_url: string, caption_text: string }
  ]
}
```

## Panel Generation (Structured JSON)
**Do not** generate images directly from the raw transcript. Instead, convert to JSON:

```json
{
  "title": "...",
  "characters": [{"name": "...", "traits": "..."}],
  "panels": [
    {"caption": "...", "image_prompt": "..."}
  ]
}
```

### Steps
1. LLM transforms transcript → JSON.
2. Validate + sanitize prompts.
3. Generate images one-by-one, store URLs.
4. Render as comic panels.

## Safety Defaults
- **Prompt-side content filter** (kid-safe constraints).
- Block obvious unsafe themes (weapons, gore, sexual content).
- No social features, no sharing.

## Next Steps
- Scaffold FastAPI service.
- Implement upload + STT pipeline.
- Add generation pipeline (LLM → images).
- Build minimal web UI.
