"""
Background task processor for sheet music conversion.

Orchestrates the full pipeline from PDF to solfa notation.
"""

import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.storage import save_job_status, get_job_dir, get_output_dir
from app.models.job import JobState
from app.pipeline.intake import PDFIntake
from app.pipeline.preprocess import ImagePreprocessor
from app.pipeline.omr.basic_omr import BasicOMREngine
from app.pipeline.omr.gemini_engine import GeminiOMREngine
from app.pipeline.symbolic import SymbolicParser
from app.pipeline.solfa import SolfaConverter
from app.pipeline.renderer import OutputRenderer

logger = logging.getLogger(__name__)


class SheetMusicProcessor:
    """
    Orchestrates the sheet music to solfa conversion pipeline.
    
    Processes PDF files through:
    1. PDF intake and page extraction
    2. Image preprocessing
    3. OMR (Optical Music Recognition) - Uses Gemini AI if available, otherwise BasicOMR
    4. Symbolic parsing
    5. Solfa conversion
    6. Output rendering
    """

    def __init__(self):
        """Initialize the processor with all pipeline components."""
        self.intake = PDFIntake()
        self.preprocessor = ImagePreprocessor()
        
        # Use Gemini if API key is available, otherwise fallback to BasicOMR
        if settings.gemini_api_key:
            self.omr_engine = GeminiOMREngine(api_key=settings.gemini_api_key)
            logger.info("Using Gemini AI for OMR (high accuracy)")
        else:
            self.omr_engine = BasicOMREngine()
            logger.info("Using BasicOMR (set GEMINI_API_KEY for better accuracy)")
        
        self.parser = SymbolicParser()
        self.converter = SolfaConverter()
        self.renderer = OutputRenderer()

    async def _update_status(
        self,
        job_id: str,
        state: JobState,
        progress: float,
        message: str = "",
        error: str | None = None,
        result: dict | None = None,
    ) -> None:
        """Update job status in storage."""
        await save_job_status(
            job_id,
            {
                "job_id": job_id,
                "state": state.value,
                "progress": progress,
                "message": message,
                "error": error,
                "result": result,
            },
        )

    async def process(self, job_id: str, pdf_path: Path) -> dict:
        """
        Process a PDF file and convert to solfa notation.
        
        Args:
            job_id: Unique job identifier
            pdf_path: Path to the input PDF file
            
        Returns:
            Dictionary with processing results
        """
        job_dir = get_job_dir(job_id)
        output_dir = get_output_dir(job_id)

        try:
            # Stage 1: PDF Intake (0-10%)
            await self._update_status(
                job_id,
                JobState.PREPROCESSING,
                5,
                "Extracting pages from PDF...",
            )

            pages_dir = job_dir / "pages"
            page_images = self.intake.process(pdf_path, pages_dir)
            
            if not page_images:
                raise ValueError("No pages could be extracted from the PDF")

            logger.info(f"Extracted {len(page_images)} pages")

            # Stage 2: Image Preprocessing (10-30%)
            await self._update_status(
                job_id,
                JobState.PREPROCESSING,
                15,
                f"Preprocessing {len(page_images)} page(s)...",
            )

            processed_dir = job_dir / "processed"
            processed_images = []
            
            for i, page_path in enumerate(page_images):
                progress = 15 + (15 * (i + 1) / len(page_images))
                await self._update_status(
                    job_id,
                    JobState.PREPROCESSING,
                    progress,
                    f"Preprocessing page {i + 1}/{len(page_images)}...",
                )
                
                output_path = processed_dir / f"processed_{page_path.name}"
                # Use lighter preprocessing for Gemini (preserves more detail)
                # Gemini Vision works better with grayscale than binary thresholded images
                if settings.gemini_api_key:
                    result = self.preprocessor.preprocess_for_gemini(page_path, output_path)
                else:
                    result = self.preprocessor.preprocess(
                        page_path, 
                        output_path,
                        apply_contrast=True,
                    )
                processed_images.append(result.processed_path)

            # Stage 3: OMR Processing (30-60%)
            await self._update_status(
                job_id,
                JobState.OMR_PROCESSING,
                35,
                "Running optical music recognition...",
            )

            omr_dir = job_dir / "omr"
            omr_results = []
            
            for i, processed_path in enumerate(processed_images):
                progress = 35 + (25 * (i + 1) / len(processed_images))
                await self._update_status(
                    job_id,
                    JobState.OMR_PROCESSING,
                    progress,
                    f"Processing page {i + 1}/{len(processed_images)} with OMR...",
                )
                
                page_omr_dir = omr_dir / f"page_{i + 1:04d}"
                omr_result = self.omr_engine.process(processed_path, page_omr_dir)
                
                if not omr_result.success:
                    logger.warning(
                        f"OMR failed for page {i + 1}: {omr_result.errors}"
                    )
                else:
                    omr_results.append(omr_result)

            if not omr_results:
                raise ValueError("OMR processing failed for all pages")

            # Stage 4: Symbolic Parsing (60-75%)
            await self._update_status(
                job_id,
                JobState.ANALYZING,
                65,
                "Parsing musical notation...",
            )

            # Parse the first successful OMR result (for monophonic MVP)
            musicxml_path = omr_results[0].musicxml_path
            if not musicxml_path or not musicxml_path.exists():
                raise ValueError("No valid MusicXML output from OMR")

            parsed_score = self.parser.parse_musicxml(musicxml_path)
            
            logger.info(
                f"Parsed {len(parsed_score.elements)} elements "
                f"from {parsed_score.metadata.total_measures} measures"
            )

            # Stage 5: Solfa Conversion (75-90%)
            await self._update_status(
                job_id,
                JobState.CONVERTING,
                80,
                "Converting to tonic solfa notation...",
            )

            solfa_result = self.converter.convert_score(parsed_score)
            
            logger.info(
                f"Converted to {len(solfa_result.measures)} measures of solfa"
            )

            # Stage 6: Output Rendering (90-100%)
            await self._update_status(
                job_id,
                JobState.RENDERING,
                92,
                "Generating output files...",
            )

            # Render text output
            txt_path = output_dir / "solfa.txt"
            txt_content = self.renderer.render(solfa_result, "txt", txt_path)
            
            # Render JSON output
            json_path = output_dir / "solfa.json"
            self.renderer.render(solfa_result, "json", json_path)
            
            # Render PDF output
            pdf_path = output_dir / "solfa.pdf"
            self.renderer.render(solfa_result, "pdf", pdf_path)

            # Get structured data for frontend
            structured_data = self.renderer.get_structured_data(solfa_result)

            # Complete
            result_data = {
                "solfa_text": txt_content if isinstance(txt_content, str) else "",
                "key_detected": str(solfa_result.key),
                "time_signature": solfa_result.time_signature,
                "measure_count": len(solfa_result.measures),
                "note_count": sum(len(m.notes) for m in solfa_result.measures),
                "available_formats": ["txt", "json", "pdf"],
                "output_dir": str(output_dir),
                "structured_data": structured_data,
            }

            await self._update_status(
                job_id,
                JobState.COMPLETED,
                100,
                "Processing complete!",
                result=result_data,
            )

            return result_data

        except Exception as e:
            logger.exception(f"Processing failed for job {job_id}: {e}")
            
            await self._update_status(
                job_id,
                JobState.FAILED,
                0,
                "Processing failed",
                error=str(e),
            )
            
            raise


# Global processor instance
processor = SheetMusicProcessor()


async def process_job(job_id: str, pdf_path: Path) -> dict:
    """
    Process a job in the background.
    
    Args:
        job_id: Unique job identifier
        pdf_path: Path to the PDF file
        
    Returns:
        Processing result dictionary
    """
    return await processor.process(job_id, pdf_path)


def process_job_sync(job_id: str, pdf_path: Path) -> dict:
    """
    Synchronous wrapper for process_job.
    
    Used when running in a thread pool or sync context.
    """
    return asyncio.run(processor.process(job_id, pdf_path))

