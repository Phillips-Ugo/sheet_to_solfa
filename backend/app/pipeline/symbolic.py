"""
Symbolic music parser using music21.

Parses MusicXML files and extracts structured musical data
into internal representations for further processing.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import music21
from music21 import converter, key, meter, stream, note, chord

from app.models.note import NoteEvent, RestEvent, MusicElement, Accidental

logger = logging.getLogger(__name__)


@dataclass
class ScoreMetadata:
    """Metadata extracted from a musical score."""

    title: str | None = None
    composer: str | None = None
    key_signature: str | None = None
    time_signature: str | None = None
    tempo: int | None = None
    total_measures: int = 0


@dataclass
class ParsedScore:
    """
    Complete parsed representation of a musical score.
    
    Contains all extracted musical elements organized by voice/part.
    """

    metadata: ScoreMetadata
    elements: list[MusicElement] = field(default_factory=list)
    key: music21.key.Key | None = None
    time_sig: music21.meter.TimeSignature | None = None

    def get_notes_by_measure(self) -> dict[int, list[MusicElement]]:
        """Group elements by measure number."""
        measures: dict[int, list[MusicElement]] = {}
        for element in self.elements:
            measure_num = element.measure_number
            if measure_num not in measures:
                measures[measure_num] = []
            measures[measure_num].append(element)
        
        # Sort notes within each measure by beat position
        for measure_num in measures:
            measures[measure_num].sort(key=lambda x: x.beat_position)
        
        return measures


class SymbolicParser:
    """
    Parser for symbolic music notation (MusicXML, MIDI).
    
    Uses music21 to parse and extract musical elements into
    our internal representation for solfa conversion.
    """

    def __init__(self):
        """Initialize the symbolic parser."""
        # Configure music21 to be less verbose
        music21.environment.set("autoDownload", "deny")

    def _accidental_from_music21(
        self, m21_accidental: music21.pitch.Accidental | None
    ) -> Accidental | None:
        """Convert music21 accidental to our Accidental enum."""
        if m21_accidental is None:
            return None

        name = m21_accidental.name.lower()
        mapping = {
            "sharp": Accidental.SHARP,
            "flat": Accidental.FLAT,
            "natural": Accidental.NATURAL,
            "double-sharp": Accidental.DOUBLE_SHARP,
            "double-flat": Accidental.DOUBLE_FLAT,
        }
        return mapping.get(name)

    def _extract_note_event(
        self,
        m21_note: music21.note.Note,
        measure_number: int,
        voice: int = 1,
    ) -> NoteEvent:
        """Convert a music21 Note to our NoteEvent."""
        # Get pitch information
        pitch = m21_note.pitch
        pitch_class = pitch.step  # C, D, E, etc.
        octave = pitch.octave

        # Get duration in quarter notes
        duration = float(m21_note.quarterLength)

        # Get beat position within measure
        beat_position = float(m21_note.beat) if m21_note.beat else 1.0

        # Get accidental
        accidental = self._accidental_from_music21(pitch.accidental)

        # Check if note is tied
        tied = m21_note.tie is not None and m21_note.tie.type in ("start", "continue")

        return NoteEvent(
            pitch_class=pitch_class,
            octave=octave if octave else 4,
            duration=duration,
            measure_number=measure_number,
            beat_position=beat_position,
            accidental=accidental,
            tied=tied,
            voice=voice,
        )

    def _extract_rest_event(
        self,
        m21_rest: music21.note.Rest,
        measure_number: int,
        voice: int = 1,
    ) -> RestEvent:
        """Convert a music21 Rest to our RestEvent."""
        duration = float(m21_rest.quarterLength)
        beat_position = float(m21_rest.beat) if m21_rest.beat else 1.0

        return RestEvent(
            duration=duration,
            measure_number=measure_number,
            beat_position=beat_position,
            voice=voice,
        )

    def _extract_elements_from_part(
        self,
        part: music21.stream.Part,
        voice_offset: int = 0,
    ) -> list[MusicElement]:
        """Extract all musical elements from a part."""
        elements: list[MusicElement] = []

        for measure in part.getElementsByClass(stream.Measure):
            measure_number = measure.number if measure.number else 1

            # Process all notes in the measure
            for element in measure.recurse().notesAndRests:
                # Get voice number
                voice_num = 1
                if hasattr(element, "voice") and element.voice:
                    voice_num = element.voice
                voice_num += voice_offset

                if isinstance(element, note.Note):
                    note_event = self._extract_note_event(
                        element, measure_number, voice_num
                    )
                    elements.append(note_event)

                elif isinstance(element, chord.Chord):
                    # For chords, extract the highest note (melody)
                    # In monophonic mode, we just take the top note
                    highest_note = element.sortAscending()[-1]
                    note_event = self._extract_note_event(
                        highest_note, measure_number, voice_num
                    )
                    elements.append(note_event)

                elif isinstance(element, note.Rest):
                    rest_event = self._extract_rest_event(
                        element, measure_number, voice_num
                    )
                    elements.append(rest_event)

        return elements

    def _extract_metadata(self, score: music21.stream.Score) -> ScoreMetadata:
        """Extract metadata from a music21 score."""
        metadata = ScoreMetadata()

        # Try to get title
        if score.metadata:
            metadata.title = score.metadata.title
            metadata.composer = score.metadata.composer

        # Get key signature from first key found
        key_sigs = list(score.recurse().getElementsByClass(key.KeySignature))
        if key_sigs:
            ks = key_sigs[0]
            if hasattr(ks, "asKey"):
                k = ks.asKey()
                metadata.key_signature = str(k)
            else:
                metadata.key_signature = f"{ks.sharps} sharps" if ks.sharps >= 0 else f"{abs(ks.sharps)} flats"

        # Get time signature
        time_sigs = list(score.recurse().getElementsByClass(meter.TimeSignature))
        if time_sigs:
            ts = time_sigs[0]
            metadata.time_signature = ts.ratioString

        # Count measures
        for part in score.parts:
            measures = part.getElementsByClass(stream.Measure)
            metadata.total_measures = max(
                metadata.total_measures,
                len(list(measures)),
            )

        # Try to get tempo
        tempos = list(score.recurse().getElementsByClass(music21.tempo.MetronomeMark))
        if tempos:
            metadata.tempo = int(tempos[0].number)

        return metadata

    def _detect_key(self, score: music21.stream.Score) -> music21.key.Key:
        """
        Detect the key of the score.
        
        First checks for explicit key signatures, then falls back
        to algorithmic key detection (Krumhansl-Schmuckler).
        """
        # Try to get explicit key signature
        key_sigs = list(score.recurse().getElementsByClass(key.Key))
        if key_sigs:
            return key_sigs[0]

        # Check for KeySignature objects and convert to Key
        key_sigs = list(score.recurse().getElementsByClass(key.KeySignature))
        if key_sigs:
            return key_sigs[0].asKey()

        # Fall back to algorithmic key detection
        try:
            detected_key = score.analyze("key")
            logger.info(f"Algorithmically detected key: {detected_key}")
            return detected_key
        except Exception as e:
            logger.warning(f"Key detection failed: {e}, defaulting to C major")
            return key.Key("C")

    def _get_time_signature(
        self, score: music21.stream.Score
    ) -> music21.meter.TimeSignature:
        """Get the primary time signature of the score."""
        time_sigs = list(score.recurse().getElementsByClass(meter.TimeSignature))
        if time_sigs:
            return time_sigs[0]
        # Default to 4/4
        return meter.TimeSignature("4/4")

    def parse_musicxml(self, musicxml_path: Path) -> ParsedScore:
        """
        Parse a MusicXML file into our internal representation.
        
        Args:
            musicxml_path: Path to the MusicXML file
            
        Returns:
            ParsedScore with all extracted musical data
        """
        logger.info(f"Parsing MusicXML: {musicxml_path}")

        # Parse the MusicXML file
        score = converter.parse(str(musicxml_path))

        # Ensure we have a Score object
        if not isinstance(score, stream.Score):
            # Wrap in a Score if needed
            new_score = stream.Score()
            new_score.append(score)
            score = new_score

        # Extract metadata
        metadata = self._extract_metadata(score)

        # Detect key and time signature
        detected_key = self._detect_key(score)
        time_sig = self._get_time_signature(score)

        # Extract all musical elements
        all_elements: list[MusicElement] = []
        
        for part_idx, part in enumerate(score.parts):
            elements = self._extract_elements_from_part(part, voice_offset=part_idx * 10)
            all_elements.extend(elements)

        # If no parts, try to extract directly from score
        if not all_elements:
            elements = self._extract_elements_from_part(score.flatten())
            all_elements.extend(elements)

        # Sort by measure number and beat position
        all_elements.sort(key=lambda x: (x.measure_number, x.beat_position))

        logger.info(
            f"Parsed {len(all_elements)} elements from {metadata.total_measures} measures"
        )

        return ParsedScore(
            metadata=metadata,
            elements=all_elements,
            key=detected_key,
            time_sig=time_sig,
        )

    def parse_midi(self, midi_path: Path) -> ParsedScore:
        """
        Parse a MIDI file into our internal representation.
        
        Args:
            midi_path: Path to the MIDI file
            
        Returns:
            ParsedScore with all extracted musical data
        """
        logger.info(f"Parsing MIDI: {midi_path}")

        # Parse the MIDI file
        score = converter.parse(str(midi_path))

        # Use the same extraction logic as MusicXML
        return self.parse_musicxml_score(score)

    def parse_musicxml_score(self, score: music21.stream.Score) -> ParsedScore:
        """
        Parse an already-loaded music21 Score object.
        
        Args:
            score: music21 Score object
            
        Returns:
            ParsedScore with all extracted musical data
        """
        # Extract metadata
        metadata = self._extract_metadata(score)

        # Detect key and time signature
        detected_key = self._detect_key(score)
        time_sig = self._get_time_signature(score)

        # Extract all musical elements
        all_elements: list[MusicElement] = []
        
        for part_idx, part in enumerate(score.parts):
            elements = self._extract_elements_from_part(part, voice_offset=part_idx * 10)
            all_elements.extend(elements)

        # Sort by measure number and beat position
        all_elements.sort(key=lambda x: (x.measure_number, x.beat_position))

        return ParsedScore(
            metadata=metadata,
            elements=all_elements,
            key=detected_key,
            time_sig=time_sig,
        )

    def parse(self, file_path: Path) -> ParsedScore:
        """
        Parse a music file (auto-detect format).
        
        Args:
            file_path: Path to the music file
            
        Returns:
            ParsedScore with all extracted musical data
        """
        suffix = file_path.suffix.lower()

        if suffix in (".musicxml", ".xml", ".mxl"):
            return self.parse_musicxml(file_path)
        elif suffix in (".mid", ".midi"):
            return self.parse_midi(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

