"""
Music Theory Engine.

Handles key detection, scale degree mapping, and chromatic alterations
for accurate tonic solfa conversion.
"""

import logging
from dataclasses import dataclass
from enum import Enum

import music21
from music21 import key, pitch, scale

from app.models.note import NoteEvent, Accidental

logger = logging.getLogger(__name__)


class Mode(str, Enum):
    """Musical mode (major or minor)."""

    MAJOR = "major"
    MINOR = "minor"


@dataclass
class ScaleDegree:
    """
    Represents a scale degree with optional chromatic alteration.
    
    Attributes:
        degree: Scale degree number (1-7)
        alteration: Chromatic alteration (+1 for raised, -1 for lowered)
        mode: The mode context (major or minor)
    """

    degree: int  # 1-7
    alteration: int = 0  # +1 = raised, -1 = lowered, 0 = natural
    mode: Mode = Mode.MAJOR

    def is_diatonic(self) -> bool:
        """Check if this is a diatonic (unaltered) scale degree."""
        return self.alteration == 0


class MusicTheoryEngine:
    """
    Engine for music theory analysis and scale degree mapping.
    
    Provides key detection, scale degree calculation, and
    chromatic alteration tracking for tonic solfa conversion.
    """

    # Pitch class to semitone mapping (C = 0)
    PITCH_TO_SEMITONE = {
        "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
    }

    # Major scale intervals (semitones from root)
    MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

    # Natural minor scale intervals
    MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

    def __init__(self):
        """Initialize the music theory engine."""
        self._current_key: key.Key | None = None
        self._key_changes: dict[int, key.Key] = {}  # measure -> key

    def set_key(self, music_key: key.Key) -> None:
        """Set the current key context."""
        self._current_key = music_key
        logger.info(f"Set key context to: {music_key}")

    def add_key_change(self, measure_number: int, new_key: key.Key) -> None:
        """Register a key change at a specific measure."""
        self._key_changes[measure_number] = new_key
        logger.info(f"Added key change at measure {measure_number}: {new_key}")

    def get_key_at_measure(self, measure_number: int) -> key.Key:
        """Get the key in effect at a specific measure."""
        # Find the most recent key change
        effective_key = self._current_key
        
        for change_measure, change_key in sorted(self._key_changes.items()):
            if change_measure <= measure_number:
                effective_key = change_key
            else:
                break
        
        return effective_key or key.Key("C")

    def get_mode(self, music_key: key.Key) -> Mode:
        """Determine if a key is major or minor."""
        if music_key.mode == "minor":
            return Mode.MINOR
        return Mode.MAJOR

    def _pitch_to_semitone(
        self, pitch_class: str, accidental: Accidental | None
    ) -> int:
        """Convert a pitch class and accidental to semitone value."""
        base = self.PITCH_TO_SEMITONE.get(pitch_class.upper(), 0)
        
        if accidental == Accidental.SHARP:
            base += 1
        elif accidental == Accidental.FLAT:
            base -= 1
        elif accidental == Accidental.DOUBLE_SHARP:
            base += 2
        elif accidental == Accidental.DOUBLE_FLAT:
            base -= 2
        
        return base % 12

    def _get_scale_semitones(self, music_key: key.Key) -> list[int]:
        """Get the semitone values for each scale degree in a key."""
        root_semitone = self.PITCH_TO_SEMITONE.get(music_key.tonic.step, 0)
        
        # Add accidental from key signature
        if music_key.tonic.accidental:
            if music_key.tonic.accidental.name == "sharp":
                root_semitone += 1
            elif music_key.tonic.accidental.name == "flat":
                root_semitone -= 1
        
        mode = self.get_mode(music_key)
        
        if mode == Mode.MINOR:
            intervals = self.MINOR_SCALE_INTERVALS
        else:
            intervals = self.MAJOR_SCALE_INTERVALS
        
        return [(root_semitone + interval) % 12 for interval in intervals]

    def get_scale_degree(
        self, note_event: NoteEvent, music_key: key.Key | None = None
    ) -> ScaleDegree:
        """
        Calculate the scale degree of a note in a given key.
        
        Args:
            note_event: The note to analyze
            music_key: The key context (uses current key if None)
            
        Returns:
            ScaleDegree with degree number and alteration
        """
        if music_key is None:
            music_key = self.get_key_at_measure(note_event.measure_number)
        
        mode = self.get_mode(music_key)
        
        # Get the semitone value of the note
        note_semitone = self._pitch_to_semitone(
            note_event.pitch_class, note_event.accidental
        )
        
        # Get the scale semitones
        scale_semitones = self._get_scale_semitones(music_key)
        
        # Find the closest scale degree
        best_degree = 1
        best_alteration = 0
        min_distance = 12
        
        for degree_idx, scale_semitone in enumerate(scale_semitones):
            distance = (note_semitone - scale_semitone) % 12
            
            # Check if this note is this scale degree
            if distance == 0:
                return ScaleDegree(degree=degree_idx + 1, alteration=0, mode=mode)
            
            # Check if raised version of this degree
            if distance == 1:
                if distance < min_distance or (distance == min_distance and degree_idx + 1 < best_degree):
                    best_degree = degree_idx + 1
                    best_alteration = 1  # Raised
                    min_distance = distance
            
            # Check if lowered version of this degree
            if distance == 11:  # One semitone below (modulo 12)
                if abs(12 - distance) < min_distance:
                    best_degree = degree_idx + 1
                    best_alteration = -1  # Lowered
                    min_distance = abs(12 - distance)
        
        return ScaleDegree(degree=best_degree, alteration=best_alteration, mode=mode)

    def get_scale_degree_music21(
        self, note_event: NoteEvent, music_key: key.Key | None = None
    ) -> ScaleDegree:
        """
        Calculate scale degree using music21's built-in methods.
        
        This provides more accurate results for complex cases.
        """
        if music_key is None:
            music_key = self.get_key_at_measure(note_event.measure_number)
        
        mode = self.get_mode(music_key)
        
        # Create a music21 pitch object
        pitch_name = note_event.pitch_class
        if note_event.accidental:
            acc_map = {
                Accidental.SHARP: "#",
                Accidental.FLAT: "-",
                Accidental.NATURAL: "",
                Accidental.DOUBLE_SHARP: "##",
                Accidental.DOUBLE_FLAT: "--",
            }
            pitch_name += acc_map.get(note_event.accidental, "")
        
        m21_pitch = pitch.Pitch(f"{pitch_name}{note_event.octave}")
        
        try:
            # Use music21's getScaleDegreeAndAccidentalFromPitch
            degree, accidental = music_key.getScaleDegreeAndAccidentalFromPitch(m21_pitch)
            
            # Determine alteration
            alteration = 0
            if accidental:
                if accidental.alter > 0:
                    alteration = 1  # Raised
                elif accidental.alter < 0:
                    alteration = -1  # Lowered
            
            return ScaleDegree(degree=degree, alteration=alteration, mode=mode)
            
        except Exception as e:
            logger.warning(f"music21 scale degree calculation failed: {e}")
            # Fall back to our own calculation
            return self.get_scale_degree(note_event, music_key)

    def detect_key_changes(
        self, notes: list[NoteEvent], window_size: int = 8
    ) -> dict[int, key.Key]:
        """
        Detect potential key changes in a sequence of notes.
        
        Uses a sliding window approach to detect modulations.
        
        Args:
            notes: List of NoteEvent objects
            window_size: Number of notes to analyze at a time
            
        Returns:
            Dictionary mapping measure numbers to detected keys
        """
        if len(notes) < window_size:
            return {}
        
        key_changes = {}
        current_key = self._current_key
        
        for i in range(0, len(notes) - window_size, window_size // 2):
            window = notes[i:i + window_size]
            
            # Create a music21 stream from the window
            s = music21.stream.Stream()
            for note_event in window:
                if isinstance(note_event, NoteEvent):
                    n = music21.note.Note()
                    n.pitch = pitch.Pitch(
                        f"{note_event.pitch_class}{note_event.octave}"
                    )
                    n.quarterLength = note_event.duration
                    s.append(n)
            
            # Analyze key
            try:
                detected = s.analyze("key")
                
                if current_key is None:
                    current_key = detected
                elif str(detected) != str(current_key):
                    # Potential key change
                    measure = window[0].measure_number
                    if measure not in key_changes:
                        key_changes[measure] = detected
                        logger.info(
                            f"Potential modulation at measure {measure}: "
                            f"{current_key} -> {detected}"
                        )
                        current_key = detected
                        
            except Exception as e:
                logger.debug(f"Key analysis failed for window: {e}")
        
        return key_changes

    def analyze_accidentals(
        self, note_event: NoteEvent, music_key: key.Key | None = None
    ) -> dict:
        """
        Analyze whether a note's accidental is chromatic or diatonic.
        
        Returns:
            Dictionary with analysis results
        """
        if music_key is None:
            music_key = self.get_key_at_measure(note_event.measure_number)
        
        scale_degree = self.get_scale_degree_music21(note_event, music_key)
        
        return {
            "note": str(note_event),
            "key": str(music_key),
            "scale_degree": scale_degree.degree,
            "alteration": scale_degree.alteration,
            "is_diatonic": scale_degree.is_diatonic(),
            "mode": scale_degree.mode.value,
        }

    def get_relative_key(self, music_key: key.Key) -> key.Key:
        """Get the relative major/minor of a key."""
        mode = self.get_mode(music_key)
        
        if mode == Mode.MAJOR:
            # Relative minor is 3 semitones below
            return music_key.relative
        else:
            # Relative major is 3 semitones above
            return music_key.relative

    def get_parallel_key(self, music_key: key.Key) -> key.Key:
        """Get the parallel major/minor of a key."""
        return music_key.parallel

