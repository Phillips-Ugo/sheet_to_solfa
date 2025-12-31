"""Musical note and event models."""

from dataclasses import dataclass
from enum import Enum
from typing import Union


class Accidental(str, Enum):
    """Musical accidentals."""

    SHARP = "sharp"
    FLAT = "flat"
    NATURAL = "natural"
    DOUBLE_SHARP = "double-sharp"
    DOUBLE_FLAT = "double-flat"


@dataclass
class NoteEvent:
    """
    Represents a single musical note event.
    
    Attributes:
        pitch_class: Note name (C, D, E, F, G, A, B)
        octave: Octave number (4 = middle C octave)
        duration: Duration in quarter note units (1.0 = quarter note)
        measure_number: Which measure this note is in (1-indexed)
        beat_position: Position within the measure (1.0 = first beat)
        accidental: Sharp, flat, or natural modifier
        tied: Whether this note is tied to the next
        voice: Voice number for polyphonic music (1 = melody)
    """

    pitch_class: str
    octave: int
    duration: float
    measure_number: int
    beat_position: float
    accidental: Accidental | None = None
    tied: bool = False
    voice: int = 1

    @property
    def midi_pitch(self) -> int:
        """Calculate MIDI pitch number (C4 = 60)."""
        pitch_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
        base = pitch_map.get(self.pitch_class.upper(), 0)
        
        # Apply accidental
        if self.accidental == Accidental.SHARP:
            base += 1
        elif self.accidental == Accidental.FLAT:
            base -= 1
        elif self.accidental == Accidental.DOUBLE_SHARP:
            base += 2
        elif self.accidental == Accidental.DOUBLE_FLAT:
            base -= 2

        return 12 * (self.octave + 1) + base

    def __str__(self) -> str:
        acc_str = ""
        if self.accidental:
            acc_map = {
                Accidental.SHARP: "#",
                Accidental.FLAT: "b",
                Accidental.NATURAL: "♮",
                Accidental.DOUBLE_SHARP: "##",
                Accidental.DOUBLE_FLAT: "bb",
            }
            acc_str = acc_map.get(self.accidental, "")
        return f"{self.pitch_class}{acc_str}{self.octave}"


@dataclass
class RestEvent:
    """
    Represents a musical rest.
    
    Attributes:
        duration: Duration in quarter note units
        measure_number: Which measure this rest is in
        beat_position: Position within the measure
        voice: Voice number
    """

    duration: float
    measure_number: int
    beat_position: float
    voice: int = 1

    def __str__(self) -> str:
        return f"rest({self.duration})"


# Type alias for any music event
MusicElement = Union[NoteEvent, RestEvent]


