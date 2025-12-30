"""
Basic OMR Engine - A computer vision based OMR implementation.

Uses OpenCV to detect:
- Staff lines
- Note heads
- Basic rhythm patterns

This is a simplified OMR that works for clean, simple sheet music.
For complex scores, use Oemer or Audiveris.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.dom import minidom

import cv2
import numpy as np

from app.pipeline.omr.base import OMREngine, OMRResult, OMRConfidence

logger = logging.getLogger(__name__)


@dataclass
class StaffSystem:
    """Represents a staff system (5 lines)."""
    
    y_positions: list[int]  # Y coordinates of the 5 staff lines
    x_start: int
    x_end: int
    line_spacing: float  # Average spacing between lines
    
    @property
    def top(self) -> int:
        return min(self.y_positions)
    
    @property
    def bottom(self) -> int:
        return max(self.y_positions)
    
    @property
    def middle_line(self) -> int:
        """Return Y position of middle (B) line."""
        return self.y_positions[2]


@dataclass
class DetectedNote:
    """A detected note from the image."""
    
    x: int  # X position
    y: int  # Y position (center)
    staff_index: int  # Which staff system
    pitch_position: float  # Position relative to staff (0 = middle line)
    is_filled: bool  # True for quarter/eighth notes, False for half/whole
    width: float
    height: float


class BasicOMREngine(OMREngine):
    """
    Basic OMR engine using computer vision.
    
    Detects staff lines and note heads to produce MusicXML output.
    Works best with clean, simple sheet music (single melody line).
    """

    # Note mapping: position on staff (0 = middle B line for treble clef)
    # Positive = above middle, Negative = below middle
    # Each integer is one staff position (line or space)
    TREBLE_CLEF_NOTES = {
        6: ("C", 6),   # High C (2 ledger lines above)
        5: ("B", 5),   # B above staff
        4: ("A", 5),   # A on top line
        3: ("G", 5),   # G in top space
        2: ("F", 5),   # F on second line from top
        1: ("E", 5),   # E in second space from top
        0: ("D", 5),   # D on middle line
        -1: ("C", 5),  # C in middle space
        -2: ("B", 4),  # B on second line from bottom
        -3: ("A", 4),  # A in second space from bottom
        -4: ("G", 4),  # G on bottom line
        -5: ("F", 4),  # F below staff
        -6: ("E", 4),  # E (1 ledger line below)
        -7: ("D", 4),  # D below ledger
        -8: ("C", 4),  # Middle C (2 ledger lines below)
    }

    def __init__(self):
        """Initialize the OMR engine."""
        self.min_staff_line_length_ratio = 0.5  # Minimum line length relative to image width
        self.note_detection_threshold = 0.6

    @property
    def name(self) -> str:
        return "BasicOMR"

    @property
    def supported_formats(self) -> list[str]:
        return ["musicxml"]

    def _detect_staff_lines(self, image: np.ndarray) -> list[StaffSystem]:
        """
        Detect staff line systems in the image.
        
        Returns list of StaffSystem objects, each containing 5 staff lines.
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        height, width = gray.shape

        # Apply binary threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Detect horizontal lines using morphology
        # Create a horizontal kernel that's about 1/4 of image width
        kernel_width = max(width // 4, 50)
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)

        # Find horizontal line contours
        contours, _ = cv2.findContours(
            horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract line information
        lines = []
        min_line_length = width * self.min_staff_line_length_ratio
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w >= min_line_length:
                lines.append({
                    "y": y + h // 2,
                    "x_start": x,
                    "x_end": x + w,
                    "width": w,
                })

        # Sort lines by y position
        lines.sort(key=lambda l: l["y"])

        # Group lines into staff systems (5 consecutive lines with similar spacing)
        staff_systems = []
        i = 0
        
        while i < len(lines) - 4:
            # Check if next 5 lines form a staff
            potential_staff = lines[i:i+5]
            
            # Calculate spacings between consecutive lines
            spacings = [
                potential_staff[j+1]["y"] - potential_staff[j]["y"]
                for j in range(4)
            ]
            
            avg_spacing = sum(spacings) / len(spacings)
            
            # Check if spacings are consistent (within 20% of average)
            if avg_spacing > 5 and all(abs(s - avg_spacing) < avg_spacing * 0.3 for s in spacings):
                # Valid staff system found
                staff = StaffSystem(
                    y_positions=[l["y"] for l in potential_staff],
                    x_start=min(l["x_start"] for l in potential_staff),
                    x_end=max(l["x_end"] for l in potential_staff),
                    line_spacing=avg_spacing,
                )
                staff_systems.append(staff)
                i += 5  # Skip these lines
            else:
                i += 1

        logger.info(f"Detected {len(staff_systems)} staff system(s)")
        return staff_systems

    def _detect_notes(
        self, image: np.ndarray, staff_systems: list[StaffSystem]
    ) -> list[DetectedNote]:
        """
        Detect note heads in the image.
        
        Uses blob detection to find circular shapes (note heads).
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Invert if needed (notes should be dark on light background)
        if np.mean(gray) < 127:
            gray = 255 - gray

        detected_notes = []

        for staff_idx, staff in enumerate(staff_systems):
            # Focus on the region around this staff
            margin = int(staff.line_spacing * 3)
            y_start = max(0, staff.top - margin)
            y_end = min(gray.shape[0], staff.bottom + margin)
            
            staff_region = gray[y_start:y_end, staff.x_start:staff.x_end]
            
            # Setup blob detector for note heads
            params = cv2.SimpleBlobDetector_Params()
            
            # Note heads are roughly circular
            params.filterByCircularity = True
            params.minCircularity = 0.5
            
            # Filter by area based on staff line spacing
            expected_note_area = (staff.line_spacing * 0.8) ** 2 * 3.14159
            params.filterByArea = True
            params.minArea = expected_note_area * 0.3
            params.maxArea = expected_note_area * 3.0
            
            # Filter by color (detect dark blobs)
            params.filterByColor = True
            params.blobColor = 0
            
            # Create detector
            detector = cv2.SimpleBlobDetector_create(params)
            
            # Detect blobs
            keypoints = detector.detect(staff_region)
            
            for kp in keypoints:
                # Convert coordinates back to full image
                note_x = int(kp.pt[0] + staff.x_start)
                note_y = int(kp.pt[1] + y_start)
                
                # Calculate pitch position relative to middle line
                pitch_pos = (staff.middle_line - note_y) / (staff.line_spacing / 2)
                
                # Determine if note is filled (quarter/eighth) or hollow (half/whole)
                # Sample the center of the blob
                local_x = int(kp.pt[0])
                local_y = int(kp.pt[1])
                if 0 <= local_y < staff_region.shape[0] and 0 <= local_x < staff_region.shape[1]:
                    center_value = staff_region[local_y, local_x]
                    is_filled = center_value < 128
                else:
                    is_filled = True
                
                detected_notes.append(DetectedNote(
                    x=note_x,
                    y=note_y,
                    staff_index=staff_idx,
                    pitch_position=round(pitch_pos),
                    is_filled=is_filled,
                    width=kp.size,
                    height=kp.size,
                ))

        # Sort notes by x position (left to right)
        detected_notes.sort(key=lambda n: n.x)
        
        logger.info(f"Detected {len(detected_notes)} note(s)")
        return detected_notes

    def _pitch_from_position(self, position: int) -> tuple[str, int]:
        """
        Convert staff position to pitch name and octave.
        
        Position 0 = middle line (B4 in treble clef)
        """
        # Clamp position to our range
        position = max(-8, min(6, int(position)))
        
        return self.TREBLE_CLEF_NOTES.get(position, ("C", 5))

    def _generate_musicxml(
        self,
        notes: list[DetectedNote],
        staff_systems: list[StaffSystem],
        output_path: Path,
    ) -> Path:
        """
        Generate MusicXML from detected notes.
        """
        # Create MusicXML structure
        score = ET.Element("score-partwise", version="4.0")

        # Part list
        part_list = ET.SubElement(score, "part-list")
        score_part = ET.SubElement(part_list, "score-part", id="P1")
        part_name = ET.SubElement(score_part, "part-name")
        part_name.text = "Detected Music"

        # Part content
        part = ET.SubElement(score, "part", id="P1")

        # Group notes into measures (roughly by x position)
        if not notes:
            # No notes detected - create one empty measure
            notes = []
        
        # Determine measure boundaries based on staff width
        if staff_systems:
            staff_width = staff_systems[0].x_end - staff_systems[0].x_start
            notes_per_measure = 4  # Assume 4/4 time
            
            # Estimate measure width
            if notes:
                avg_note_spacing = staff_width / max(len(notes), 1)
                measure_width = avg_note_spacing * notes_per_measure
            else:
                measure_width = staff_width / 4
        else:
            measure_width = 200
        
        # Group notes into measures
        measures_notes: list[list[DetectedNote]] = []
        current_measure: list[DetectedNote] = []
        measure_start_x = notes[0].x if notes else 0
        
        for note in notes:
            if note.x > measure_start_x + measure_width and current_measure:
                measures_notes.append(current_measure)
                current_measure = [note]
                measure_start_x = note.x
            else:
                current_measure.append(note)
        
        if current_measure:
            measures_notes.append(current_measure)
        
        # Ensure at least one measure
        if not measures_notes:
            measures_notes = [[]]

        # Generate XML for each measure
        for measure_num, measure_notes in enumerate(measures_notes, 1):
            measure = ET.SubElement(part, "measure", number=str(measure_num))

            # Add attributes in first measure
            if measure_num == 1:
                attributes = ET.SubElement(measure, "attributes")
                
                divisions = ET.SubElement(attributes, "divisions")
                divisions.text = "1"

                key = ET.SubElement(attributes, "key")
                fifths = ET.SubElement(key, "fifths")
                fifths.text = "0"  # C major (we don't detect key yet)

                time = ET.SubElement(attributes, "time")
                beats = ET.SubElement(time, "beats")
                beats.text = "4"
                beat_type = ET.SubElement(time, "beat-type")
                beat_type.text = "4"

                clef = ET.SubElement(attributes, "clef")
                sign = ET.SubElement(clef, "sign")
                sign.text = "G"
                line = ET.SubElement(clef, "line")
                line.text = "2"

            # Add notes in this measure
            if not measure_notes:
                # Add a rest for empty measures
                note_elem = ET.SubElement(measure, "note")
                rest = ET.SubElement(note_elem, "rest")
                duration = ET.SubElement(note_elem, "duration")
                duration.text = "4"
                note_type = ET.SubElement(note_elem, "type")
                note_type.text = "whole"
            else:
                for detected_note in measure_notes:
                    note_elem = ET.SubElement(measure, "note")
                    
                    # Get pitch from position
                    pitch_name, octave = self._pitch_from_position(
                        int(detected_note.pitch_position)
                    )
                    
                    pitch = ET.SubElement(note_elem, "pitch")
                    step = ET.SubElement(pitch, "step")
                    step.text = pitch_name
                    octave_elem = ET.SubElement(pitch, "octave")
                    octave_elem.text = str(octave)

                    duration = ET.SubElement(note_elem, "duration")
                    duration.text = "1"  # Quarter note

                    note_type = ET.SubElement(note_elem, "type")
                    note_type.text = "quarter"

        # Pretty print XML
        xml_str = ET.tostring(score, encoding="unicode")
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Add DOCTYPE
        final_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        final_xml += '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
        lines = pretty_xml.split("\n")[1:]
        final_xml += "\n".join(lines)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_xml)

        return output_path

    def process(self, image_path: Path, output_dir: Path) -> OMRResult:
        """
        Process a sheet music image using computer vision.
        """
        if not self.validate_image(image_path):
            return OMRResult(
                success=False,
                errors=[f"Invalid image file: {image_path}"],
            )

        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                return OMRResult(
                    success=False,
                    errors=[f"Could not load image: {image_path}"],
                )

            logger.info(f"Processing image: {image_path.name} ({image.shape[1]}x{image.shape[0]})")

            # Step 1: Detect staff lines
            staff_systems = self._detect_staff_lines(image)
            
            if not staff_systems:
                return OMRResult(
                    success=False,
                    errors=["No staff lines detected in the image"],
                    warnings=["Make sure the image contains visible staff lines"],
                )

            # Step 2: Detect notes
            notes = self._detect_notes(image, staff_systems)
            
            if not notes:
                logger.warning("No notes detected - generating empty score")

            # Step 3: Generate MusicXML
            output_dir.mkdir(parents=True, exist_ok=True)
            musicxml_path = output_dir / "score.musicxml"
            
            self._generate_musicxml(notes, staff_systems, musicxml_path)

            # Determine confidence based on detection quality
            if len(notes) > 10:
                confidence = OMRConfidence.MEDIUM
            elif len(notes) > 0:
                confidence = OMRConfidence.LOW
            else:
                confidence = OMRConfidence.LOW

            return OMRResult(
                success=True,
                musicxml_path=musicxml_path,
                confidence=confidence,
                warnings=[
                    "BasicOMR uses simple computer vision - results may vary",
                    "For best results, use clean scans with clear notation",
                ] if len(notes) < 5 else [],
                metadata={
                    "staff_systems_detected": len(staff_systems),
                    "notes_detected": len(notes),
                    "measures_generated": max(1, len(notes) // 4),
                    "image_size": (image.shape[1], image.shape[0]),
                },
            )

        except Exception as e:
            logger.exception(f"OMR processing failed: {e}")
            return OMRResult(
                success=False,
                errors=[f"OMR processing failed: {str(e)}"],
            )
