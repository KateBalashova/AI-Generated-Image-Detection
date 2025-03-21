# -*- coding: utf-8 -*-
"""PatchCraft ELA

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1kQvt3p_LWZvhk65BdSzGKPz1W4D7KcSe
"""

import numpy as np
from PIL import Image, ImageChops, ImageEnhance
from scipy.ndimage import gaussian_filter
from skimage.feature import local_binary_pattern
import os

def calculate_texture_richness(image, patch_size=8):
    """
    Calculate texture richness for each patch in the image.

    Args:
        image: PIL Image object
        patch_size: Size of patches to analyze (default=8)

    Returns:
        numpy array of texture richness scores
    """
    # Convert to grayscale and numpy array
    if isinstance(image, Image.Image):
        img_gray = np.array(image.convert('L'))
    else:
        img_gray = np.array(image)

    # Calculate LBP for texture analysis
    radius = 2
    n_points = 8 * radius
    lbp = local_binary_pattern(img_gray, n_points, radius, method='uniform')

    # Initialize texture richness map
    height, width = img_gray.shape
    richness_map = np.zeros((height // patch_size, width // patch_size))

    # Calculate variance for each patch
    for i in range(0, height - patch_size + 1, patch_size):
        for j in range(0, width - patch_size + 1, patch_size):
            patch = lbp[i:i+patch_size, j:j+patch_size]
            # Combine LBP histogram variance with intensity variance
            texture_score = np.var(patch)
            richness_map[i//patch_size, j//patch_size] = texture_score

    return richness_map

def separate_textures(image, threshold_percentile=70):
    """
    Separate image into rich and poor texture regions.

    Args:
        image: PIL Image object
        threshold_percentile: Percentile for texture separation (default=70)

    Returns:
        tuple of (rich_texture_mask, poor_texture_mask)
    """
    # Calculate texture richness
    richness_map = calculate_texture_richness(image)

    # Upscale richness map to original image size
    height, width = np.array(image).shape[:2]
    richness_map_resized = Image.fromarray(richness_map).resize(
        (width, height), Image.Resampling.BILINEAR)
    richness_map = np.array(richness_map_resized)

    # Calculate threshold
    threshold = np.percentile(richness_map, threshold_percentile)

    # Create masks
    rich_mask = richness_map >= threshold
    poor_mask = ~rich_mask

    return rich_mask, poor_mask

def perform_ela(image, quality=90):
    """
    Performs Error Level Analysis on an input image.

    Args:
        image: PIL Image object or path to image
        quality: JPEG compression quality (1-100, default=90)

    Returns:
        PIL Image object containing the ELA result
    """
    # Handle both file path and PIL Image inputs
    if isinstance(image, str):
        original = Image.open(image)
    else:
        original = image

    # Convert to RGB if necessary
    if original.mode != 'RGB':
        original = original.convert('RGB')

    # Create temporary filename for JPEG conversion
    temp_fname = 'temp_ela.jpg'

    # Save image with specified quality
    original.save(temp_fname, 'JPEG', quality=quality)

    # Open temporary image
    recompressed = Image.open(temp_fname)

    # Calculate the difference
    ela_image = ImageChops.difference(original, recompressed)

    # Enhance the difference for better visualization
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1

    # Scale the difference
    scale = 255.0 / max_diff
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)

    # Clean up temporary file
    os.remove(temp_fname)

    return ela_image

def patchcraft_ela_analysis(image_path, output_dir, ela_quality=90):
    """
    Perform PatchCraft texture separation followed by ELA analysis.

    Args:
        image_path: Path to input image
        output_dir: Directory to save results
        ela_quality: Quality for ELA JPEG compression (default=90)

    Returns:
        dict containing paths to output images
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load image
    original = Image.open(image_path)

    # Separate textures
    rich_mask, poor_mask = separate_textures(original)

    # Convert masks to PIL images
    rich_mask_img = Image.fromarray((rich_mask * 255).astype(np.uint8))
    poor_mask_img = Image.fromarray((poor_mask * 255).astype(np.uint8))

    # Apply masks to original image
    rich_texture = Image.composite(original, Image.new('RGB', original.size, 'black'), rich_mask_img)
    poor_texture = Image.composite(original, Image.new('RGB', original.size, 'black'), poor_mask_img)

    # Perform ELA on both regions
    rich_ela = perform_ela(rich_texture, quality=ela_quality)
    poor_ela = perform_ela(poor_texture, quality=ela_quality)

    # Save results
    output_paths = {}

    # Save texture masks
    rich_mask_path = os.path.join(output_dir, 'rich_texture_mask.png')
    poor_mask_path = os.path.join(output_dir, 'poor_texture_mask.png')
    rich_mask_img.save(rich_mask_path)
    poor_mask_img.save(poor_mask_path)
    output_paths['rich_mask'] = rich_mask_path
    output_paths['poor_mask'] = poor_mask_path

    # Save separated textures
    rich_texture_path = os.path.join(output_dir, 'rich_texture.png')
    poor_texture_path = os.path.join(output_dir, 'poor_texture.png')
    rich_texture.save(rich_texture_path)
    poor_texture.save(poor_texture_path)
    output_paths['rich_texture'] = rich_texture_path
    output_paths['poor_texture'] = poor_texture_path

    # Save ELA results
    rich_ela_path = os.path.join(output_dir, 'rich_texture_ela.png')
    poor_ela_path = os.path.join(output_dir, 'poor_texture_ela.png')
    rich_ela.save(rich_ela_path)
    poor_ela.save(poor_ela_path)
    output_paths['rich_ela'] = rich_ela_path
    output_paths['poor_ela'] = poor_ela_path

    return output_paths