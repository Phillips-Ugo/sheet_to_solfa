"""
Tonic Solfa Conversion Engine.

Converts musical notes to tonic solfa notation using the movable-do system.
Supports major and minor keys with chromatic alterations.
"""

import logging
from dataclasses import dataclass

import music21
from music21 import key

from app.models.note import NoteEvent, RestEvent, MusicElement
from app.models.solfa import SolfaSyllable, SolfaNote, SolfaMeasure, SolfaResult
from app.pipeline.theory import MusicTheoryEngine, ScaleDegree, Mode
from app.pipeline.symbolic import ParsedScore

logger = logging.getLogger(__name__)


# Reference octave for solfa (middle C octave = 4)
REFERENCE_OCTAVE = 4


@dataclass
class SolfaConversionConfig:
    """Configuration for solfa conversion."""

    # Whether to use la-based minor (True) or do-based minor (False)
    la_based_minor: bool = True
    
    # Reference octave for determining high/low modifiers
    reference_octave: int = REFERENCE_OCTAVE
    
    # Whether to show rests in output
    show_rests: bool = True
    
    # Use abbreviated syllables (d, r, m) or full (do, re, mi)
    use_abbreviated: bool = True


class SolfaConverter:
    """
    Converter for tonic solfa notation.
    
    Implements the movable-do system with support for:
    - Major and minor keys
    - Chromatic alterations (di, ra, fi, te, etc.)
    - Octave modifiers (apostrophe for high, comma for low)
    - La-based minor mode
    """

    # Major scale syllables (1-7)
    MAJOR_SYLLABLES = {
        1: SolfaSyllable.DO,
        2: SolfaSyllable.RE,
        3: SolfaSyllable.MI,
        4: SolfaSyllable.FA,
        5: SolfaSyllable.SOL,
        6: SolfaSyllable.LA,
        7: SolfaSyllable.TI,
    }

    # Raised chromatic syllables (sharp versions)
    RAISED_SYLLABLES = {
        1: SolfaSyllable.DI,   # Raised do
        2: SolfaSyllable.RI,   # Raised re
        4: SolfaSyllable.FI,   # Raised fa
        5: SolfaSyllable.SI,   # Raised sol
        6: SolfaSyllable.LI,   # Raised la
    }

    # Lowered chromatic syllables (flat versions)
    LOWERED_SYLLABLES = {
        2: SolfaSyllable.RA,   # Lowered re
        3: SolfaSyllable.ME,   # Lowered mi
        5: SolfaSyllable.SE,   # Lowered sol
        6: SolfaSyllable.LE,   # Lowered la
        7: SolfaSyllable.TE,   # Lowered ti
    }

    # La-based minor mapping (minor scale degrees to solfa)
    # In la-based minor, the tonic (1) of minor = la (6) of relative major
    MINOR_TO_MAJOR_DEGREE = {
        1: 6,  # la
        2: 7,  # ti
        3: 1,  # do
        4: 2,  # re
        5: 3,  # mi
        6: 4,  # fa
        7: 5,  # sol
    }

    def __init__(self, config: SolfaConversionConfig | None = None):
        """
        Initialize the solfa converter.
        
        Args:
            config: Conversion configuration options
        """
        self.config = config or SolfaConversionConfig()
        self.theory_engine = MusicTheoryEngine()

    def _get_syllable_for_degree(
        self, scale_degree: ScaleDegree
    ) -> SolfaSyllable:
        """
        Get the solfa syllable for a scale degree.
        
        Handles chromatic alterations and minor mode conversion.
        """
        degree = scale_degree.degree
        alteration = scale_degree.alteration
        mode = scale_degree.mode

        # Convert to major-relative degree for la-based minor
        if mode == Mode.MINOR and self.config.la_based_minor:
            degree = self.MINOR_TO_MAJOR_DEGREE.get(degree, degree)

        # Handle chromatic alterations
        if alteration > 0:  # Raised
            if degree in self.RAISED_SYLLABLES:
                return self.RAISED_SYLLABLES[degree]
            # Fall back to diatonic if no raised version exists
            return self.MAJOR_SYLLABLES.get(degree, SolfaSyllable.DO)
        
        elif alteration < 0:  # Lowered
            if degree in self.LOWERED_SYLLABLES:
                return self.LOWERED_SYLLABLES[degree]
            # Fall back to diatonic if no lowered version exists
            return self.MAJOR_SYLLABLES.get(degree, SolfaSyllable.DO)
        
        else:  # Diatonic
            return self.MAJOR_SYLLABLES.get(degree, SolfaSyllable.DO)

    def _get_octave_modifier(
        self, note_event: NoteEvent, music_key: key.Key
    ) -> str:
        """
        Calculate the octave modifier for a note.
        
        Returns:
            "'" for notes above reference octave
            "," for notes below reference octave
            "" for notes in reference octave
        """
        # Get the reference octave (the octave containing the tonic)
        ref_octave = self.config.reference_octave
        
        # Calculate octave difference
        octave_diff = note_event.octave - ref_octave
        
        if octave_diff > 0:
            # Higher octave(s) - use apostrophes
            return "'" * octave_diff
        elif octave_diff < 0:
            # Lower octave(s) - use commas
            return "," * abs(octave_diff)
        else:
            return ""

    def convert_note(
        self, note_event: NoteEvent, music_key: key.Key
    ) -> SolfaNote:
        """
        Convert a single note to solfa notation.
        
        Args:
            note_event: The note to convert
            music_key: The key context
            
        Returns:
            SolfaNote with syllable and modifiers
        """
        # Get scale degree using music theory engine
        scale_degree = self.theory_engine.get_scale_degree_music21(
            note_event, music_key
        )
        
        # Get syllable
        syllable = self._get_syllable_for_degree(scale_degree)
        
        # Get octave modifier
        octave_modifier = self._get_octave_modifier(note_event, music_key)
        
        return SolfaNote(
            syllable=syllable,
            octave_modifier=octave_modifier,
            duration_beats=note_event.duration,
            is_tied=note_event.tied,
            is_rest=False,
        )

    def convert_rest(self, rest_event: RestEvent) -> SolfaNote:
        """Convert a rest to solfa notation."""
        return SolfaNote(
            syllable=SolfaSyllable.REST,
            duration_beats=rest_event.duration,
            is_rest=True,
        )

    def convert_element(
        self, element: MusicElement, music_key: key.Key
    ) -> SolfaNote:
        """Convert any music element to solfa notation."""
        if isinstance(element, NoteEvent):
            return self.convert_note(element, music_key)
        elif isinstance(element, RestEvent):
            return self.convert_rest(element)
        else:
            # Unknown element type, return a rest
            return SolfaNote(
                syllable=SolfaSyllable.REST,
                is_rest=True,
            )

    def convert_score(self, parsed_score: ParsedScore) -> SolfaResult:
        """
        Convert a complete parsed score to solfa notation.
        
        Args:
            parsed_score: The parsed musical score
            
        Returns:
            SolfaResult with all converted measures
        """
        # Set up the theory engine with the detected key
        music_key = parsed_score.key or key.Key("C")
        self.theory_engine.set_key(music_key)
        
        # Get time signature info
        time_sig = parsed_score.time_sig
        time_sig_tuple = (
            (time_sig.numerator, time_sig.denominator)
            if time_sig else (4, 4)
        )
        time_sig_str = f"{time_sig_tuple[0]}/{time_sig_tuple[1]}"
        
        # Group elements by measure
        elements_by_measure = parsed_score.get_notes_by_measure()
        
        # Convert each measure
        measures = []
        for measure_num in sorted(elements_by_measure.keys()):
            elements = elements_by_measure[measure_num]
            
            # Get the key for this measure (handles modulations)
            current_key = self.theory_engine.get_key_at_measure(measure_num)
            
            # Convert each element in the measure
            solfa_notes = []
            for element in elements:
                if isinstance(element, RestEvent) and not self.config.show_rests:
                    continue
                solfa_note = self.convert_element(element, current_key)
                solfa_notes.append(solfa_note)
            
            if solfa_notes:  # Only add measures with notes
                measure = SolfaMeasure(
                    measure_number=measure_num,
                    notes=solfa_notes,
                    time_signature=time_sig_tuple,
                )
                measures.append(measure)
        
        return SolfaResult(
            measures=measures,
            key=str(music_key),
            time_signature=time_sig_str,
            title=parsed_score.metadata.title or "",
        )

    def format_solfa_line(
        self, measure: SolfaMeasure, abbreviated: bool = True
    ) -> str:
        """
        Format a single measure as a solfa text line.
        
        Args:
            measure: The measure to format
            abbreviated: Use short syllables (d, r, m) vs full (do, re, mi)
            
        Returns:
            Formatted string representation
        """
        parts = []
        
        for note in measure.notes:
            if abbreviated:
                text = note.syllable.value + note.octave_modifier
            else:
                # Full syllable names
                full_names = {
                    "d": "do", "r": "re", "m": "mi", "f": "fa",
                    "s": "sol", "l": "la", "t": "ti",
                    "di": "di", "ri": "ri", "fi": "fi", "si": "si", "li": "li",
                    "ra": "ra", "me": "me", "se": "se", "le": "le", "te": "te",
                    "0": "rest",
                }
                base = full_names.get(note.syllable.value, note.syllable.value)
                text = base + note.octave_modifier
            
            # Handle duration (sustained notes)
            if note.duration_beats > 1.0:
                text += " -" * (int(note.duration_beats) - 1)
            elif note.duration_beats == 0.5:
                text = f"({text})"  # Half beat in parentheses
            
            parts.append(text)
        
        return " ".join(parts)

    def to_text(self, result: SolfaResult, measures_per_line: int = 4) -> str:
        """
        Convert solfa result to plain text format.
        
        Args:
            result: The solfa conversion result
            measures_per_line: Number of measures per text line
            
        Returns:
            Formatted text string
        """
        lines = []
        
        # Header
        if result.title:
            lines.append(f"# {result.title}")
            lines.append("")
        
        lines.append(f"Key: {result.key}")
        lines.append(f"Time: {result.time_signature}")
        lines.append("")
        
        # Format measures
        current_line = []
        for i, measure in enumerate(result.measures):
            measure_text = self.format_solfa_line(
                measure, self.config.use_abbreviated
            )
            current_line.append(measure_text)
            
            if (i + 1) % measures_per_line == 0:
                lines.append("| " + " | ".join(current_line) + " |")
                current_line = []
        
        # Handle remaining measures
        if current_line:
            lines.append("| " + " | ".join(current_line) + " |")
        
        return "\n".join(lines)


