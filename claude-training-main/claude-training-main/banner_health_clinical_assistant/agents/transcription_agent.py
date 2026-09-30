"""Simulated ASR (speech-to-text) agent.

Doc reference: 01-banner-health-clinical-documentation.md, component "Speech-to-Text (ASR)"
and key processing step #1 ("segment audio into rolling transcript chunks").

There is no real microphone/audio pipeline in this demo, so `transcribe()` takes
already-dictated text (standing in for ambient audio) and simulates the ASR
step by splitting it into per-sentence segments with a synthetic confidence score.
"""

from __future__ import annotations

import random
import re
from typing import List

from agents.base import BaseAgent
from models import Encounter, SpeakerRole, TranscriptSegment

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


class TranscriptionAgent(BaseAgent):
    name = "TranscriptionAgent"

    def transcribe(self, encounter: Encounter, raw_dictation_text: str) -> List[TranscriptSegment]:
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(raw_dictation_text.strip()) if s.strip()]

        rng = random.Random(encounter.id)  # deterministic confidence per encounter
        segments: List[TranscriptSegment] = []
        for i, sentence in enumerate(sentences):
            segments.append(
                TranscriptSegment(
                    encounter_id=encounter.id,
                    sequence=i,
                    text=sentence,
                    speaker_role=SpeakerRole.CLINICIAN,
                    confidence=round(rng.uniform(0.89, 0.99), 3),
                )
            )
        return segments
