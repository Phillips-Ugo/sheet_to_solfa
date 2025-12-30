"""
Output Renderer.

Renders solfa conversion results to various output formats:
- Plain text
- JSON
- PDF
"""

import json
import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.models.solfa import SolfaResult, SolfaMeasure

logger = logging.getLogger(__name__)


class OutputRenderer:
    """
    Renders solfa results to various output formats.
    
    Supported formats:
    - Plain text (.txt)
    - JSON (.json)
    - PDF (.pdf)
    """

    def __init__(self, measures_per_line: int = 4):
        """
        Initialize the output renderer.
        
        Args:
            measures_per_line: Number of measures per line in text/PDF output
        """
        self.measures_per_line = measures_per_line

    def _format_measure(self, measure: SolfaMeasure) -> str:
        """Format a single measure as text."""
        parts = []
        for note in measure.notes:
            text = note.syllable.value + note.octave_modifier
            
            # Handle duration indicators
            if note.duration_beats >= 2.0:
                text += " -" * (int(note.duration_beats) - 1)
            elif note.duration_beats == 0.5:
                text = f"({text})"
            
            parts.append(text)
        
        return " ".join(parts)

    def render_text(self, result: SolfaResult) -> str:
        """
        Render solfa result to plain text format.
        
        Args:
            result: The solfa conversion result
            
        Returns:
            Formatted plain text string
        """
        lines = []
        
        # Header
        if result.title:
            lines.append(f"# {result.title}")
            lines.append("")
        
        lines.append(f"Key: {result.key}")
        lines.append(f"Time Signature: {result.time_signature}")
        lines.append(f"Measures: {len(result.measures)}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")
        
        # Format measures
        current_line = []
        for i, measure in enumerate(result.measures):
            measure_text = self._format_measure(measure)
            current_line.append(measure_text)
            
            if (i + 1) % self.measures_per_line == 0:
                lines.append("| " + " | ".join(current_line) + " |")
                current_line = []
        
        # Handle remaining measures
        if current_line:
            lines.append("| " + " | ".join(current_line) + " |")
        
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return "\n".join(lines)

    def render_json(self, result: SolfaResult, pretty: bool = True) -> str:
        """
        Render solfa result to JSON format.
        
        Args:
            result: The solfa conversion result
            pretty: Whether to format with indentation
            
        Returns:
            JSON string
        """
        data = self.get_structured_data(result)
        
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    def get_structured_data(self, result: SolfaResult) -> dict[str, Any]:
        """
        Get structured data representation for frontend consumption.
        
        Args:
            result: The solfa conversion result
            
        Returns:
            Dictionary with structured measure and note data
        """
        data = {
            "title": result.title,
            "key": result.key,
            "time_signature": result.time_signature,
            "measure_count": len(result.measures),
            "generated_at": datetime.utcnow().isoformat(),
            "measures": [],
        }
        
        for measure in result.measures:
            measure_data = {
                "number": measure.measure_number,
                "text": self._format_measure(measure),
                "notes": [
                    {
                        "syllable": note.syllable.value,
                        "octave_modifier": note.octave_modifier,
                        "duration": note.duration_beats,
                        "is_rest": note.is_rest,
                        "display": note.to_string(),
                    }
                    for note in measure.notes
                ],
            }
            data["measures"].append(measure_data)
        
        return data

    def render_pdf(
        self,
        result: SolfaResult,
        output_path: Path | None = None,
        page_size: tuple = A4,
    ) -> bytes | None:
        """
        Render solfa result to PDF format.
        
        Args:
            result: The solfa conversion result
            output_path: Path to save PDF (if None, returns bytes)
            page_size: Page size tuple (default A4)
            
        Returns:
            PDF bytes if output_path is None, else None
        """
        # Create buffer or file
        if output_path:
            buffer = str(output_path)
        else:
            buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=20,
            alignment=1,  # Center
        )
        
        header_style = ParagraphStyle(
            "Header",
            parent=styles["Normal"],
            fontSize=12,
            spaceAfter=6,
        )
        
        solfa_style = ParagraphStyle(
            "Solfa",
            parent=styles["Normal"],
            fontSize=14,
            fontName="Courier",
            spaceAfter=12,
            spaceBefore=6,
            leading=20,
        )
        
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.gray,
        )
        
        # Build document content
        story = []
        
        # Title
        if result.title:
            story.append(Paragraph(result.title, title_style))
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("Tonic Solfa Notation", title_style))
            story.append(Spacer(1, 20))
        
        # Metadata
        story.append(Paragraph(f"<b>Key:</b> {result.key}", header_style))
        story.append(
            Paragraph(f"<b>Time Signature:</b> {result.time_signature}", header_style)
        )
        story.append(
            Paragraph(f"<b>Measures:</b> {len(result.measures)}", header_style)
        )
        story.append(Spacer(1, 30))
        
        # Solfa notation
        current_line = []
        for i, measure in enumerate(result.measures):
            measure_text = self._format_measure(measure)
            current_line.append(measure_text)
            
            if (i + 1) % self.measures_per_line == 0:
                line_text = "| " + " | ".join(current_line) + " |"
                story.append(Paragraph(line_text, solfa_style))
                current_line = []
        
        # Handle remaining measures
        if current_line:
            line_text = "| " + " | ".join(current_line) + " |"
            story.append(Paragraph(line_text, solfa_style))
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(
            Paragraph(
                f"Generated by Sheet to Solfa - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                footer_style,
            )
        )
        
        # Build PDF
        doc.build(story)
        
        # Return bytes if no output path
        if output_path is None:
            return buffer.getvalue()
        
        return None

    def render(
        self,
        result: SolfaResult,
        format: str,
        output_path: Path | None = None,
    ) -> str | bytes:
        """
        Render solfa result to the specified format.
        
        Args:
            result: The solfa conversion result
            format: Output format ('txt', 'json', 'pdf')
            output_path: Optional path to save output
            
        Returns:
            Rendered output (string for txt/json, bytes for pdf)
        """
        format = format.lower().strip(".")
        
        if format in ("txt", "text"):
            content = self.render_text(result)
            if output_path:
                output_path.write_text(content, encoding="utf-8")
            return content
        
        elif format == "json":
            content = self.render_json(result)
            if output_path:
                output_path.write_text(content, encoding="utf-8")
            return content
        
        elif format == "pdf":
            if output_path:
                self.render_pdf(result, output_path)
                return output_path.read_bytes()
            return self.render_pdf(result)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

    def save_all_formats(
        self,
        result: SolfaResult,
        output_dir: Path,
        base_name: str = "solfa",
    ) -> dict[str, Path]:
        """
        Save solfa result in all supported formats.
        
        Args:
            result: The solfa conversion result
            output_dir: Directory to save files
            base_name: Base filename (without extension)
            
        Returns:
            Dictionary mapping format to output path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        # Text
        txt_path = output_dir / f"{base_name}.txt"
        self.render("txt", result, txt_path)
        outputs["txt"] = txt_path
        
        # JSON
        json_path = output_dir / f"{base_name}.json"
        self.render("json", result, json_path)
        outputs["json"] = json_path
        
        # PDF
        pdf_path = output_dir / f"{base_name}.pdf"
        self.render("pdf", result, pdf_path)
        outputs["pdf"] = pdf_path
        
        logger.info(f"Saved outputs to {output_dir}: {list(outputs.keys())}")
        
        return outputs

