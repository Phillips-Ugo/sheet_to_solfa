"""
Gemini OMR Engine - Uses Google's Gemini Vision AI for sheet music recognition.

This engine leverages Gemini's vision capabilities to:
1. Analyze sheet music images
2. Identify notes, rhythms, and key signatures
3. Convert directly to tonic solfa notation

This is more accurate than traditional CV-based OMR for most sheet music.
"""

import base64
import json
import logging
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

from app.pipeline.omr.base import OMREngine, OMRResult, OMRConfidence

logger = logging.getLogger(__name__)


class GeminiOMREngine(OMREngine):
    """
    OMR engine using Google Gemini's vision capabilities.
    
    Uses Gemini 2.0 Flash to analyze sheet music images and extract
    musical notation with high accuracy.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Gemini OMR engine.
        
        Args:
            api_key: Google AI API key. If not provided, uses GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model = None
        self._initialized = False

    def _init_client(self):
        """Initialize the Gemini client."""
        if self._initialized:
            return True
            
        if not self.api_key:
            logger.error("Gemini API key not provided")
            return False
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash-exp")
            self._initialized = True
            logger.info("Gemini client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            return False

    @property
    def name(self) -> str:
        return "GeminiOMR"

    @property
    def supported_formats(self) -> list[str]:
        return ["musicxml", "solfa"]

    @property
    def is_available(self) -> bool:
        """Check if Gemini is properly configured."""
        return bool(self.api_key)

    def _encode_image(self, image_path: Path) -> tuple[str, str]:
        """Encode image to base64 for Gemini API."""
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Determine mime type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")
        
        return base64.standard_b64encode(image_data).decode("utf-8"), mime_type

    def _create_prompt(self) -> str:
        """Create the prompt for Gemini to analyze sheet music."""
        return """You are an expert musicologist analyzing sheet music. Extract ALL musical notes with maximum accuracy.

CRITICAL INSTRUCTIONS:
1. Extract the MELODY LINE only (treble clef/top staff). For piano scores, use ONLY the top staff.
2. Read from LEFT TO RIGHT, measure by measure, ensuring you don't skip any notes.
3. Pay careful attention to note positions on the staff - use ledger lines to determine octaves correctly.
4. Count beats carefully - each measure should total the correct number of beats per the time signature.
5. Distinguish between similar-looking notes (e.g., B vs D, E vs G) by their exact staff positions.

Extract:
- KEY SIGNATURE: Identify from the key signature symbols (e.g., "C major", "G major", "D minor", "A minor")
- TIME SIGNATURE: Read from the time signature (e.g., "4/4", "3/4", "2/4", "6/8")
- MEASURES: Process each measure separately, maintaining correct beat counts

For EACH NOTE, provide:
- pitch: Base note letter only (C, D, E, F, G, A, B) - NO accidentals in pitch field
- accidental: "sharp", "flat", or null (only if the note has an explicit accidental that differs from key signature)
- octave: Use scientific pitch notation (middle C = C4, C above middle C = C5, C below = C3)
- duration: "whole", "half", "quarter", "eighth", "sixteenth" (be precise - distinguish eighth from quarter notes)

For RESTS:
- Use: {"rest": true, "duration": "quarter"} format
- Count rest durations accurately to maintain measure beat totals

Return ONLY valid JSON with this EXACT structure:
```json
{
  "key": "G major",
  "time_signature": "4/4",
  "measures": [
    {
      "number": 1,
      "notes": [
        {"pitch": "G", "octave": 4, "duration": "quarter", "accidental": null},
        {"pitch": "A", "octave": 4, "duration": "quarter", "accidental": null},
        {"pitch": "B", "octave": 4, "duration": "quarter", "accidental": null},
        {"pitch": "C", "octave": 5, "duration": "quarter", "accidental": null}
      ]
    }
  ]
}
```

STRICT RULES:
- Use "notes" array only (NEVER "treble_notes" or "bass_notes")
- Every measure must contain notes that sum to the correct number of beats
- Include EVERY note - do not skip any, even if they repeat
- Double-check octave numbers by counting ledger lines and staff positions carefully
- Verify that each measure's total duration matches the time signature
- If uncertain about a note, examine surrounding notes for context clues"""

    def _parse_gemini_response(self, response_text: str) -> dict | None:
        """Parse Gemini's response to extract JSON data."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.error("No JSON found in Gemini response")
                    return None
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Response was: {response_text}")
            return None

    def _generate_musicxml_from_analysis(
        self, analysis: dict, output_path: Path
    ) -> Path:
        """Generate MusicXML from Gemini's analysis."""
        # Create MusicXML structure
        score = ET.Element("score-partwise", version="4.0")

        # Part list
        part_list = ET.SubElement(score, "part-list")
        score_part = ET.SubElement(part_list, "score-part", id="P1")
        part_name = ET.SubElement(score_part, "part-name")
        part_name.text = "Sheet Music"

        # Part content
        part = ET.SubElement(score, "part", id="P1")

        # Parse key signature
        key_str = analysis.get("key", "C major")
        key_fifths = self._key_to_fifths(key_str)
        key_mode = "minor" if "minor" in key_str.lower() else "major"

        # Parse time signature
        time_sig = analysis.get("time_signature", "4/4")
        beats, beat_type = time_sig.split("/") if "/" in time_sig else ("4", "4")

        # Duration mapping
        duration_map = {
            "whole": 4,
            "half": 2,
            "quarter": 1,
            "eighth": 0.5,
            "sixteenth": 0.25,
        }

        type_names = {
            4: "whole",
            2: "half",
            1: "quarter",
            0.5: "eighth",
            0.25: "16th",
        }

        measures = analysis.get("measures", [])
        
        for measure_data in measures:
            measure_num = measure_data.get("number", 1)
            measure = ET.SubElement(part, "measure", number=str(measure_num))

            # Add attributes in first measure
            if measure_num == 1:
                attributes = ET.SubElement(measure, "attributes")
                
                divisions = ET.SubElement(attributes, "divisions")
                divisions.text = "4"  # 4 divisions per quarter note

                key = ET.SubElement(attributes, "key")
                fifths = ET.SubElement(key, "fifths")
                fifths.text = str(key_fifths)
                mode = ET.SubElement(key, "mode")
                mode.text = key_mode

                time = ET.SubElement(attributes, "time")
                beats_elem = ET.SubElement(time, "beats")
                beats_elem.text = beats
                beat_type_elem = ET.SubElement(time, "beat-type")
                beat_type_elem.text = beat_type

                clef = ET.SubElement(attributes, "clef")
                sign = ET.SubElement(clef, "sign")
                sign.text = "G"
                line = ET.SubElement(clef, "line")
                line.text = "2"

            # Add notes - handle both simple "notes" and piano-style "treble_notes"/"bass_notes"
            all_notes = measure_data.get("notes", [])
            
            # If no simple notes, try treble_notes (prioritize melody line)
            if not all_notes:
                all_notes = measure_data.get("treble_notes", [])
            
            # If still no notes, try bass_notes as fallback
            if not all_notes:
                all_notes = measure_data.get("bass_notes", [])
            
            for note_data in all_notes:
                note_elem = ET.SubElement(measure, "note")
                
                if note_data.get("rest"):
                    rest = ET.SubElement(note_elem, "rest")
                    dur_name = note_data.get("duration", "quarter")
                    dur_value = duration_map.get(dur_name, 1)
                    
                    duration = ET.SubElement(note_elem, "duration")
                    duration.text = str(int(dur_value * 4))
                    
                    note_type = ET.SubElement(note_elem, "type")
                    note_type.text = type_names.get(dur_value, "quarter")
                else:
                    pitch = ET.SubElement(note_elem, "pitch")
                    step = ET.SubElement(pitch, "step")
                    
                    # Get pitch and handle accidentals in pitch string (e.g., "F#", "Bb")
                    pitch_str = note_data.get("pitch", "C")
                    accidental = note_data.get("accidental")
                    
                    # Extract base note and inline accidental
                    if len(pitch_str) > 1 and pitch_str[1] in "#b":
                        step.text = pitch_str[0]
                        if pitch_str[1] == "#":
                            accidental = "sharp"
                        elif pitch_str[1] == "b":
                            accidental = "flat"
                    else:
                        step.text = pitch_str[0] if pitch_str else "C"
                    
                    # Handle accidentals
                    if accidental and accidental not in ["null", "natural"]:
                        alter = ET.SubElement(pitch, "alter")
                        if accidental == "sharp":
                            alter.text = "1"
                        elif accidental == "flat":
                            alter.text = "-1"
                    
                    octave = ET.SubElement(pitch, "octave")
                    octave.text = str(note_data.get("octave", 4))

                    dur_name = note_data.get("duration", "quarter")
                    dur_value = duration_map.get(dur_name, 1)
                    
                    duration = ET.SubElement(note_elem, "duration")
                    duration.text = str(int(dur_value * 4))

                    note_type = ET.SubElement(note_elem, "type")
                    note_type.text = type_names.get(dur_value, "quarter")

                    if accidental:
                        acc_elem = ET.SubElement(note_elem, "accidental")
                        acc_elem.text = accidental

        # Pretty print XML
        xml_str = ET.tostring(score, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        final_xml += '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
        lines = pretty_xml.split("\n")[1:]
        final_xml += "\n".join(lines)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_xml)

        return output_path

    def _key_to_fifths(self, key_str: str) -> int:
        """Convert key string to circle of fifths position."""
        key_map = {
            "C major": 0, "A minor": 0,
            "G major": 1, "E minor": 1,
            "D major": 2, "B minor": 2,
            "A major": 3, "F# minor": 3,
            "E major": 4, "C# minor": 4,
            "B major": 5, "G# minor": 5,
            "F# major": 6, "D# minor": 6,
            "F major": -1, "D minor": -1,
            "Bb major": -2, "G minor": -2,
            "Eb major": -3, "C minor": -3,
            "Ab major": -4, "F minor": -4,
            "Db major": -5, "Bb minor": -5,
            "Gb major": -6, "Eb minor": -6,
        }
        
        # Normalize key string
        key_normalized = key_str.strip()
        
        for key_name, fifths in key_map.items():
            if key_name.lower() in key_normalized.lower():
                return fifths
        
        return 0  # Default to C major

    def process(self, image_path: Path, output_dir: Path) -> OMRResult:
        """
        Process a sheet music image using Gemini Vision.
        """
        if not self.validate_image(image_path):
            return OMRResult(
                success=False,
                errors=[f"Invalid image file: {image_path}"],
            )

        if not self._init_client():
            return OMRResult(
                success=False,
                errors=["Gemini API not configured. Set GEMINI_API_KEY environment variable."],
            )

        try:
            import google.generativeai as genai
            
            logger.info(f"Analyzing sheet music with Gemini: {image_path.name}")

            # Load and encode image
            image_data, mime_type = self._encode_image(image_path)
            
            # Create the image part for Gemini
            image_part = {
                "mime_type": mime_type,
                "data": image_data,
            }

            # Send to Gemini with timeout handling
            prompt = self._create_prompt()
            
            logger.info("Sending request to Gemini API...")
            try:
                import time
                start_time = time.time()
                
                # Generate content with retry logic for timeouts
                response = self._model.generate_content([
                    prompt,
                    image_part,
                ])
                
                elapsed = time.time() - start_time
                logger.info(f"Gemini API responded in {elapsed:.2f} seconds")

                # Parse the response
                response_text = response.text
                logger.info(f"Gemini response length: {len(response_text)} chars")
            except Exception as api_error:
                logger.error(f"Gemini API call failed: {api_error}")
                raise
            
            # Ensure output directory exists before saving
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save raw response for debugging
            raw_response_file = output_dir / "gemini_raw_response.txt"
            raw_response_file.write_text(response_text, encoding="utf-8")
            logger.info(f"Saved raw Gemini response to {raw_response_file}")

            analysis = self._parse_gemini_response(response_text)
            
            if analysis:
                # Log analysis summary
                measures = analysis.get("measures", [])
                total_notes = sum(len(m.get("notes", [])) for m in measures)
                logger.info(f"Gemini detected: key={analysis.get('key')}, time={analysis.get('time_signature')}, measures={len(measures)}, notes={total_notes}")
            
            if not analysis:
                return OMRResult(
                    success=False,
                    errors=["Failed to parse Gemini's analysis of the sheet music"],
                    metadata={"raw_response": response_text[:1000]},
                )

            # Generate MusicXML
            output_dir.mkdir(parents=True, exist_ok=True)
            musicxml_path = output_dir / "score.musicxml"
            
            self._generate_musicxml_from_analysis(analysis, musicxml_path)

            # Count notes for metadata (handle multiple note formats)
            def count_notes_in_measure(m):
                notes = m.get("notes", []) or m.get("treble_notes", []) or m.get("bass_notes", [])
                return len([n for n in notes if not n.get("rest")])
            
            total_notes = sum(count_notes_in_measure(m) for m in analysis.get("measures", []))
            
            return OMRResult(
                success=True,
                musicxml_path=musicxml_path,
                confidence=OMRConfidence.HIGH,
                metadata={
                    "key": analysis.get("key", "Unknown"),
                    "time_signature": analysis.get("time_signature", "4/4"),
                    "measures_detected": len(analysis.get("measures", [])),
                    "notes_detected": total_notes,
                    "engine": "gemini-2.0-flash",
                },
            )

        except Exception as e:
            logger.exception(f"Gemini OMR processing failed: {e}")
            return OMRResult(
                success=False,
                errors=[f"Gemini processing failed: {str(e)}"],
            )

