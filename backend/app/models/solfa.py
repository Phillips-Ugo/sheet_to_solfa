"""Tonic solfa notation models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SolfaSyllable(str, Enum):
    """Standard solfa syllables with chromatic alterations."""

    # Major scale degrees
    DO = "d"
    RE = "r"
    MI = "m"
    FA = "f"
    SOL = "s"
    LA = "l"
    TI = "t"

    # Raised chromatic alterations
    DI = "di"  # Raised do
    RI = "ri"  # Raised re
    FI = "fi"  # Raised fa
    SI = "si"  # Raised sol
    LI = "li"  # Raised la

    # Lowered chromatic alterations
    RA = "ra"  # Lowered re
    ME = "me"  # Lowered mi (also used in minor)
    SE = "se"  # Lowered sol
    LE = "le"  # Lowered la
    TE = "te"  # Lowered ti

    # Rest
    REST = "0"


@dataclass
class SolfaNote:
    """
    A single tonic solfa notation element.
    
    Attributes:
        syllable: The solfa syllable
        octave_modifier: Apostrophe for high, comma for low (e.g., d' or d,)
        duration_beats: Duration in beats
        is_tied: Whether tied to next note
        is_rest: Whether this is a rest
    """

    syllable: SolfaSyllable
    octave_modifier: str = ""  # "'" for high, "," for low
    duration_beats: float = 1.0
    is_tied: bool = False
    is_rest: bool = False

    def to_string(self) -> str:
        """Convert to display string."""
        if self.is_rest:
            return "0"
        
        base = self.syllable.value + self.octave_modifier
        
        # Add duration indicators
        if self.duration_beats >= 2.0:
            # Sustained notes shown with dashes
            dashes = int(self.duration_beats) - 1
            return base + " " + " -" * dashes
        
        return base


@dataclass
class SolfaMeasure:
    """A single measure of solfa notation."""

    measure_number: int
    notes: list[SolfaNote] = field(default_factory=list)
    time_signature: tuple[int, int] = (4, 4)

    def to_string(self) -> str:
        """Convert measure to display string."""
        note_strs = [n.to_string() for n in self.notes]
        return " ".join(note_strs)


@dataclass
class SolfaResult:
    """Complete solfa conversion result."""

    measures: list[SolfaMeasure] = field(default_factory=list)
    key: str = "C major"
    time_signature: str = "4/4"
    title: str = ""

    def to_text(self) -> str:
        """Convert to plain text format."""
        lines = []
        
        if self.title:
            lines.append(f"# {self.title}")
            lines.append("")
        
        lines.append(f"Key: {self.key}")
        lines.append(f"Time: {self.time_signature}")
        lines.append("")

        # Group measures into lines (4 measures per line)
        current_line = []
        for i, measure in enumerate(self.measures):
            current_line.append(measure.to_string())
            if (i + 1) % 4 == 0:
                lines.append("| " + " | ".join(current_line) + " |")
                current_line = []

        # Handle remaining measures
        if current_line:
            lines.append("| " + " | ".join(current_line) + " |")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "title": self.title,
            "key": self.key,
            "time_signature": self.time_signature,
            "measure_count": len(self.measures),
            "measures": [
                {
                    "number": m.measure_number,
                    "notes": [
                        {
                            "syllable": n.syllable.value,
                            "octave_modifier": n.octave_modifier,
                            "duration": n.duration_beats,
                            "is_rest": n.is_rest,
                        }
                        for n in m.notes
                    ],
                }
                for m in self.measures
            ],
        }

