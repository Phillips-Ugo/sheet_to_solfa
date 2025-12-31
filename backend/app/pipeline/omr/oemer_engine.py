"""
Oemer OMR Engine - Integration with the Oemer Python OMR library.

Oemer is a deep learning-based Optical Music Recognition system.
https://github.com/BreezeWhite/oemer

Note: Oemer requires additional setup and model downloads.
This module provides the integration layer.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.pipeline.omr.base import OMREngine, OMRResult, OMRConfidence

logger = logging.getLogger(__name__)


class OemerEngine(OMREngine):
    """
    OMR engine using Oemer (End-to-end Optical Music Recognition).
    
    Oemer uses deep learning to recognize:
    - Staff lines and measures
    - Note heads and stems
    - Accidentals
    - Clefs and key signatures
    - Time signatures
    """

    def __init__(self):
        """Initialize the Oemer engine."""
        self._oemer_available = self._check_oemer_available()
        if not self._oemer_available:
            logger.warning(
                "Oemer is not installed. Install with: pip install oemer"
            )

    def _check_oemer_available(self) -> bool:
        """Check if Oemer is available."""
        try:
            import oemer  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def name(self) -> str:
        return "Oemer"

    @property
    def supported_formats(self) -> list[str]:
        return ["musicxml", "midi"]

    @property
    def is_available(self) -> bool:
        """Check if Oemer is properly installed and ready to use."""
        return self._oemer_available

    def process(self, image_path: Path, output_dir: Path) -> OMRResult:
        """
        Process a sheet music image using Oemer.
        
        Args:
            image_path: Path to the preprocessed sheet music image
            output_dir: Directory to save output files
            
        Returns:
            OMRResult with paths to generated MusicXML and MIDI files
        """
        if not self.validate_image(image_path):
            return OMRResult(
                success=False,
                errors=[f"Invalid image file: {image_path}"],
            )

        if not self._oemer_available:
            return OMRResult(
                success=False,
                errors=["Oemer is not installed. Install with: pip install oemer"],
            )

        try:
            # Import oemer
            from oemer import generate_musicxml
            from oemer.inference import inference

            output_dir.mkdir(parents=True, exist_ok=True)

            # Run Oemer inference
            logger.info(f"Running Oemer on {image_path}")
            
            # Create a temporary directory for Oemer output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy input image to temp directory
                temp_image = temp_path / image_path.name
                shutil.copy(image_path, temp_image)

                # Run inference
                try:
                    # Oemer's inference function
                    result = inference(str(temp_image))
                    
                    # Generate MusicXML from the result
                    musicxml_content = generate_musicxml(result)
                    
                    # Save MusicXML
                    musicxml_path = output_dir / "score.musicxml"
                    with open(musicxml_path, "w", encoding="utf-8") as f:
                        f.write(musicxml_content)

                    return OMRResult(
                        success=True,
                        musicxml_path=musicxml_path,
                        confidence=OMRConfidence.MEDIUM,
                        metadata={
                            "engine": "oemer",
                            "source_image": str(image_path),
                        },
                    )

                except Exception as e:
                    logger.error(f"Oemer inference failed: {e}")
                    return OMRResult(
                        success=False,
                        errors=[f"Oemer inference failed: {str(e)}"],
                    )

        except Exception as e:
            logger.exception(f"Oemer processing failed: {e}")
            return OMRResult(
                success=False,
                errors=[f"Oemer processing failed: {str(e)}"],
            )


class OemerCLIEngine(OMREngine):
    """
    OMR engine using Oemer via command-line interface.
    
    This is an alternative to the Python API integration,
    useful when running Oemer in a separate environment.
    """

    def __init__(self, oemer_path: str = "oemer"):
        """
        Initialize the Oemer CLI engine.
        
        Args:
            oemer_path: Path to the oemer command or virtual environment
        """
        self.oemer_path = oemer_path

    @property
    def name(self) -> str:
        return "OemerCLI"

    @property
    def supported_formats(self) -> list[str]:
        return ["musicxml"]

    def process(self, image_path: Path, output_dir: Path) -> OMRResult:
        """
        Process a sheet music image using Oemer CLI.
        """
        if not self.validate_image(image_path):
            return OMRResult(
                success=False,
                errors=[f"Invalid image file: {image_path}"],
            )

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Run oemer command
            cmd = [
                self.oemer_path,
                str(image_path),
                "-o", str(output_dir),
            ]

            logger.info(f"Running Oemer CLI: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                return OMRResult(
                    success=False,
                    errors=[f"Oemer CLI failed: {result.stderr}"],
                )

            # Find the generated MusicXML file
            musicxml_files = list(output_dir.glob("*.musicxml")) + list(
                output_dir.glob("*.xml")
            )
            
            if not musicxml_files:
                return OMRResult(
                    success=False,
                    errors=["Oemer did not generate MusicXML output"],
                )

            return OMRResult(
                success=True,
                musicxml_path=musicxml_files[0],
                confidence=OMRConfidence.MEDIUM,
                metadata={
                    "engine": "oemer-cli",
                    "source_image": str(image_path),
                },
            )

        except subprocess.TimeoutExpired:
            return OMRResult(
                success=False,
                errors=["Oemer CLI timed out after 5 minutes"],
            )
        except FileNotFoundError:
            return OMRResult(
                success=False,
                errors=[f"Oemer command not found: {self.oemer_path}"],
            )
        except Exception as e:
            logger.exception(f"Oemer CLI processing failed: {e}")
            return OMRResult(
                success=False,
                errors=[f"Oemer CLI processing failed: {str(e)}"],
            )


