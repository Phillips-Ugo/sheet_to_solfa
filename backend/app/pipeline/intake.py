"""PDF intake and page extraction module."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Generator

import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFType(str, Enum):
    """Type of PDF document."""

    VECTOR = "vector"  # Native digital PDF with vector graphics
    RASTER = "raster"  # Scanned/image-based PDF
    MIXED = "mixed"  # Contains both vector and raster content


@dataclass
class PDFInfo:
    """Information about a PDF document."""

    path: Path
    pdf_type: PDFType
    page_count: int
    title: str | None = None
    author: str | None = None


class PDFIntake:
    """
    PDF intake and preprocessing handler.
    
    Handles both vector (native digital) and raster (scanned) PDFs,
    extracting pages as images for OMR processing.
    """

    def __init__(self, dpi: int = None):
        """
        Initialize PDF intake handler.
        
        Args:
            dpi: Resolution for image extraction (default from settings)
        """
        self.dpi = dpi or settings.pdf_dpi

    def analyze_pdf(self, pdf_path: Path) -> PDFInfo:
        """
        Analyze a PDF to determine its type and properties.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            PDFInfo with document details
        """
        doc = fitz.open(pdf_path)

        try:
            # Check if PDF contains mostly images or vectors
            total_images = 0
            total_vectors = 0

            for page_num in range(min(doc.page_count, 5)):  # Check first 5 pages
                page = doc[page_num]

                # Count image objects
                images = page.get_images()
                total_images += len(images)

                # Check for vector content (text and drawings)
                text = page.get_text()
                drawings = page.get_drawings()
                if text.strip() or drawings:
                    total_vectors += 1

            # Determine PDF type
            if total_images > 0 and total_vectors == 0:
                pdf_type = PDFType.RASTER
            elif total_images == 0 and total_vectors > 0:
                pdf_type = PDFType.VECTOR
            elif total_images > 0 and total_vectors > 0:
                pdf_type = PDFType.MIXED
            else:
                # Default to raster if we can't determine
                pdf_type = PDFType.RASTER

            # Extract metadata
            metadata = doc.metadata
            title = metadata.get("title") if metadata else None
            author = metadata.get("author") if metadata else None

            return PDFInfo(
                path=pdf_path,
                pdf_type=pdf_type,
                page_count=doc.page_count,
                title=title,
                author=author,
            )

        finally:
            doc.close()

    def extract_pages(
        self, pdf_path: Path, output_dir: Path
    ) -> Generator[Path, None, None]:
        """
        Extract all pages from PDF as images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            
        Yields:
            Path to each extracted page image
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(pdf_path)

        try:
            for page_num in range(doc.page_count):
                page = doc[page_num]

                # Calculate zoom factor for desired DPI
                # Default PDF resolution is 72 DPI
                zoom = self.dpi / 72.0
                matrix = fitz.Matrix(zoom, zoom)

                # Render page to pixmap
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)

                # Convert to PIL Image
                img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

                # Save as PNG
                output_path = output_dir / f"page_{page_num + 1:04d}.png"
                img.save(output_path, "PNG", optimize=True)

                logger.info(f"Extracted page {page_num + 1}/{doc.page_count}: {output_path}")
                yield output_path

        finally:
            doc.close()

    def extract_single_page(
        self, pdf_path: Path, page_number: int, output_path: Path
    ) -> Path:
        """
        Extract a single page from PDF as image.
        
        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract (1-indexed)
            output_path: Path to save the extracted image
            
        Returns:
            Path to the extracted image
        """
        doc = fitz.open(pdf_path)

        try:
            if page_number < 1 or page_number > doc.page_count:
                raise ValueError(
                    f"Page {page_number} out of range (1-{doc.page_count})"
                )

            page = doc[page_number - 1]

            # Calculate zoom factor for desired DPI
            zoom = self.dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            # Convert to PIL Image and save
            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG", optimize=True)

            return output_path

        finally:
            doc.close()

    def process(self, pdf_path: Path, output_dir: Path) -> list[Path]:
        """
        Process a PDF file and extract all pages as images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images
            
        Returns:
            List of paths to extracted page images
        """
        info = self.analyze_pdf(pdf_path)
        logger.info(
            f"Processing PDF: {info.page_count} pages, type: {info.pdf_type.value}"
        )

        return list(self.extract_pages(pdf_path, output_dir))


