"""Image preprocessing module for sheet music images."""

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingResult:
    """Result of image preprocessing."""

    original_path: Path
    processed_path: Path
    was_deskewed: bool
    rotation_angle: float
    original_size: tuple[int, int]
    processed_size: tuple[int, int]


class ImagePreprocessor:
    """
    Preprocesses sheet music images for optimal OMR performance.
    
    Applies various image processing techniques including:
    - Grayscale conversion
    - Adaptive thresholding
    - Deskewing
    - Noise removal
    """

    def __init__(
        self,
        threshold_block_size: int = 15,
        threshold_c: int = 10,
        deskew_angle_limit: float = 10.0,
    ):
        """
        Initialize the image preprocessor.
        
        Args:
            threshold_block_size: Block size for adaptive thresholding (must be odd)
            threshold_c: Constant subtracted from mean in thresholding
            deskew_angle_limit: Maximum angle (degrees) to attempt deskewing
        """
        # Ensure block size is odd
        if threshold_block_size % 2 == 0:
            threshold_block_size += 1
        
        self.threshold_block_size = threshold_block_size
        self.threshold_c = threshold_c
        self.deskew_angle_limit = deskew_angle_limit

    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale if needed."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def apply_adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive Gaussian thresholding.
        
        This helps handle varying lighting conditions across the page.
        """
        gray = self.to_grayscale(image)
        
        return cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            self.threshold_block_size,
            self.threshold_c,
        )

    def detect_skew_angle(self, image: np.ndarray) -> float:
        """
        Detect the skew angle of the image using Hough transform.
        
        Returns:
            Skew angle in degrees (positive = counterclockwise)
        """
        gray = self.to_grayscale(image)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)
        
        if lines is None or len(lines) == 0:
            return 0.0
        
        # Calculate angles of detected lines
        angles = []
        for line in lines[:50]:  # Limit to first 50 lines for performance
            rho, theta = line[0]
            # Convert to degrees, adjusting for horizontal lines
            angle = (theta * 180 / np.pi) - 90
            
            # Only consider small angles (staff lines should be roughly horizontal)
            if abs(angle) < self.deskew_angle_limit:
                angles.append(angle)
        
        if not angles:
            return 0.0
        
        # Return median angle for robustness
        return float(np.median(angles))

    def deskew(self, image: np.ndarray, angle: float = None) -> tuple[np.ndarray, float]:
        """
        Deskew the image by rotating to correct for tilt.
        
        Args:
            image: Input image
            angle: Rotation angle in degrees. If None, auto-detect.
            
        Returns:
            Tuple of (deskewed image, rotation angle applied)
        """
        if angle is None:
            angle = self.detect_skew_angle(image)
        
        if abs(angle) < 0.1:  # Skip if negligible rotation needed
            return image, 0.0
        
        # Get image dimensions
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Calculate rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new bounding box size
        cos = abs(rotation_matrix[0, 0])
        sin = abs(rotation_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust rotation matrix for new size
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]
        
        # Apply rotation with white background
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (new_w, new_h),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255) if len(image.shape) == 3 else 255,
        )
        
        return rotated, angle

    def remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise using morphological operations.
        
        Applies opening (erosion followed by dilation) to remove small noise
        while preserving larger features like staff lines and notes.
        """
        gray = self.to_grayscale(image)
        
        # Small kernel for noise removal
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        
        # Opening removes small white noise in black regions
        opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        
        # Closing removes small black noise in white regions
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        
        return cleaned

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE.
        
        Contrast Limited Adaptive Histogram Equalization helps
        improve visibility of faint or low-contrast notation.
        """
        gray = self.to_grayscale(image)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def preprocess_for_gemini(
        self,
        input_path: Path,
        output_path: Path,
    ) -> PreprocessingResult:
        """
        Light preprocessing optimized for Gemini Vision.
        Gemini works better with grayscale/color images rather than binary thresholded.
        """
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        original_size = (image.shape[1], image.shape[0])
        
        # Convert to grayscale
        processed = self.to_grayscale(image)
        
        # Apply contrast enhancement (helps Gemini see details better)
        processed = self.enhance_contrast(processed)
        
        # Light deskewing only (don't want to lose quality)
        processed, rotation_angle = self.deskew(processed)
        was_deskewed = abs(rotation_angle) >= 0.1
        
        processed_size = (processed.shape[1], processed.shape[0])
        
        # Save as grayscale (not binary thresholded)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), processed)
        
        logger.info(f"Preprocessed for Gemini: {input_path.name} -> {output_path.name}")
        
        return PreprocessingResult(
            original_path=input_path,
            processed_path=output_path,
            was_deskewed=was_deskewed,
            rotation_angle=rotation_angle,
            original_size=original_size,
            processed_size=processed_size,
        )

    def preprocess(
        self,
        input_path: Path,
        output_path: Path,
        apply_threshold: bool = True,
        apply_deskew: bool = True,
        apply_noise_removal: bool = True,
        apply_contrast: bool = True,  # Default to True for better OMR accuracy
    ) -> PreprocessingResult:
        """
        Apply full preprocessing pipeline to an image.
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            apply_threshold: Whether to apply adaptive thresholding
            apply_deskew: Whether to attempt deskewing
            apply_noise_removal: Whether to remove noise
            apply_contrast: Whether to enhance contrast (before thresholding)
            
        Returns:
            PreprocessingResult with details about the processing
        """
        # Load image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        original_size = (image.shape[1], image.shape[0])
        rotation_angle = 0.0
        was_deskewed = False

        # Convert to grayscale for processing
        processed = self.to_grayscale(image)
        
        # Apply contrast enhancement if requested
        if apply_contrast:
            processed = self.enhance_contrast(processed)
        
        # Deskew
        if apply_deskew:
            processed, rotation_angle = self.deskew(processed)
            was_deskewed = abs(rotation_angle) >= 0.1
            if was_deskewed:
                logger.info(f"Deskewed by {rotation_angle:.2f} degrees")
        
        # Apply adaptive threshold
        if apply_threshold:
            processed = self.apply_adaptive_threshold(processed)
        
        # Remove noise
        if apply_noise_removal:
            processed = self.remove_noise(processed)
        
        processed_size = (processed.shape[1], processed.shape[0])
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), processed)
        
        logger.info(f"Preprocessed {input_path.name} -> {output_path.name}")
        
        return PreprocessingResult(
            original_path=input_path,
            processed_path=output_path,
            was_deskewed=was_deskewed,
            rotation_angle=rotation_angle,
            original_size=original_size,
            processed_size=processed_size,
        )

    def process_batch(
        self, input_paths: list[Path], output_dir: Path, **kwargs
    ) -> list[PreprocessingResult]:
        """
        Process multiple images.
        
        Args:
            input_paths: List of input image paths
            output_dir: Directory to save processed images
            **kwargs: Additional arguments passed to preprocess()
            
        Returns:
            List of PreprocessingResult objects
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        
        for input_path in input_paths:
            output_path = output_dir / f"processed_{input_path.name}"
            result = self.preprocess(input_path, output_path, **kwargs)
            results.append(result)
        
        return results

