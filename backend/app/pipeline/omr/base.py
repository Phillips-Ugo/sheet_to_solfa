"""Abstract base class for OMR engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class OMRConfidence(str, Enum):
    """Confidence level of OMR recognition."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class OMRResult:
    """Result from OMR processing."""

    success: bool
    musicxml_path: Path | None = None
    midi_path: Path | None = None
    confidence: OMRConfidence = OMRConfidence.UNKNOWN
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class OMREngine(ABC):
    """
    Abstract base class for Optical Music Recognition engines.
    
    Implementations should process sheet music images and output
    structured music data (MusicXML or MIDI).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this OMR engine."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Return list of supported output formats (e.g., ['musicxml', 'midi'])."""
        pass

    @abstractmethod
    def process(self, image_path: Path, output_dir: Path) -> OMRResult:
        """
        Process a sheet music image.
        
        Args:
            image_path: Path to the preprocessed sheet music image
            output_dir: Directory to save output files
            
        Returns:
            OMRResult with paths to generated files and metadata
        """
        pass

    def process_batch(
        self, image_paths: list[Path], output_dir: Path
    ) -> list[OMRResult]:
        """
        Process multiple sheet music images.
        
        Default implementation processes sequentially.
        Subclasses may override for parallel processing.
        
        Args:
            image_paths: List of paths to preprocessed images
            output_dir: Directory to save output files
            
        Returns:
            List of OMRResult objects
        """
        results = []
        for i, image_path in enumerate(image_paths):
            page_output = output_dir / f"page_{i + 1:04d}"
            page_output.mkdir(parents=True, exist_ok=True)
            result = self.process(image_path, page_output)
            results.append(result)
        return results

    def validate_image(self, image_path: Path) -> bool:
        """
        Validate that an image can be processed.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if image is valid for processing
        """
        if not image_path.exists():
            return False
        
        valid_extensions = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
        return image_path.suffix.lower() in valid_extensions

