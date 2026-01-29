#!/usr/bin/env python3
"""
Background Removal Script
Removes backgrounds from all images in a directory and subdirectories.
Converts images to PNG format with transparent backgrounds.
"""

import os
from PIL import Image
import argparse
from pathlib import Path


def remove_background_color_based(image_path, threshold=240, edge_threshold=10, preserve_watermark=True):
    """
    Removes background based on color similarity to corners.
    Assumes corners represent the background color.
    Preserves watermarks by detecting darker pixels that might be watermark content.
    
    Args:
        image_path: Path to the image file
        threshold: Brightness threshold for background removal (0-255)
        edge_threshold: Threshold for edge detection smoothing
        preserve_watermark: If True, preserves darker pixels that might be watermarks
    
    Returns:
        PIL Image with transparent background
    """
    img = Image.open(image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Get corner pixels to determine background color
    width, height = img.size
    corners = [
        img.getpixel((0, 0)),  # Top-left
        img.getpixel((width-1, 0)),  # Top-right
        img.getpixel((0, height-1)),  # Bottom-left
        img.getpixel((width-1, height-1))  # Bottom-right
    ]
    
    # Calculate average background color from corners
    avg_r = sum(c[0] for c in corners if len(c) >= 3) // len(corners)
    avg_g = sum(c[1] for c in corners if len(c) >= 3) // len(corners)
    avg_b = sum(c[2] for c in corners if len(c) >= 3) // len(corners)
    
    # Watermark detection threshold
    watermark_threshold = threshold - 50
    
    # Create new image with transparency
    data = img.getdata()
    new_data = []
    
    for item in data:
        if len(item) >= 3:
            r, g, b = item[0], item[1], item[2]
            a = item[3] if len(item) > 3 else 255
            
            # Calculate distance from background color
            color_distance = ((r - avg_r)**2 + (g - avg_g)**2 + (b - avg_b)**2)**0.5
            
            # Calculate brightness
            brightness = (r + g + b) / 3
            
            # Check if pixel is grayscale (very lenient)
            # Very lenient: allow up to 40 difference between channels
            grayscale_threshold = 40
            is_grayscale = abs(r - g) < grayscale_threshold and abs(g - b) < grayscale_threshold and abs(r - b) < grayscale_threshold
            
            if preserve_watermark:
                # Preserve ALL grayscale pixels as potential watermarks
                # Only remove pure white or very bright colored pixels
                if is_grayscale:
                    # This is a grayscale pixel - preserve it as watermark
                    watermark_gray = int(brightness)
                    # Calculate alpha based on brightness
                    if brightness >= threshold:
                        # Very light gray (almost white) - make it more transparent
                        alpha = int(100 + (255 - brightness) / (255 - threshold + 1) * 100)
                        alpha = max(100, min(200, alpha))
                    else:
                        # Darker gray - more opaque
                        alpha = int(150 + (threshold - brightness) / threshold * 105)
                        alpha = max(150, min(255, alpha))
                    new_data.append((watermark_gray, watermark_gray, watermark_gray, alpha))
                elif color_distance < edge_threshold or brightness > threshold:
                    # Background color -> transparent
                    new_data.append((r, g, b, 0))
                else:
                    # Keep pixel with original alpha
                    new_data.append((r, g, b, a))
            else:
                # Original behavior
                if color_distance < edge_threshold or brightness > threshold:
                    new_data.append((r, g, b, 0))
                else:
                    new_data.append((r, g, b, a))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    return img


def remove_background_brightness_based(image_path, threshold=240, preserve_watermark=True):
    """
    Removes background based on brightness threshold.
    Preserves watermarks by detecting darker pixels that might be watermark content.
    
    Args:
        image_path: Path to the image file
        threshold: Brightness threshold (0-255)
        preserve_watermark: If True, preserves darker pixels that might be watermarks
    
    Returns:
        PIL Image with transparent background
    """
    img = Image.open(image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    width, height = img.size
    data = img.getdata()
    new_data = []
    
    # Watermark preservation: preserve ALL grayscale pixels aggressively
    # Strategy: Keep ALL grayscale pixels, only remove pure white/very bright colored pixels
    # Very lenient grayscale detection: allow up to 40 difference between channels
    grayscale_threshold = 40
    
    for i, item in enumerate(data):
        if len(item) >= 3:
            r, g, b = item[0], item[1], item[2]
            brightness = (r + g + b) / 3
            
            # Check if pixel is grayscale (very lenient)
            is_grayscale = abs(r - g) < grayscale_threshold and abs(g - b) < grayscale_threshold and abs(r - b) < grayscale_threshold
            
            if preserve_watermark:
                # Preserve ALL grayscale pixels as potential watermarks
                # Only remove pure white or very bright colored pixels
                if is_grayscale:
                    # This is a grayscale pixel - preserve it as watermark
                    # Even very light grays should be preserved
                    watermark_gray = int(brightness)
                    # Calculate alpha based on brightness
                    # Very light grays (close to white) get lower alpha, darker grays get higher alpha
                    # Map brightness range (0-255) to alpha range (100-255)
                    if brightness >= threshold:
                        # Very light gray (almost white) - make it more transparent
                        alpha = int(100 + (255 - brightness) / (255 - threshold + 1) * 100)
                        alpha = max(100, min(200, alpha))
                    else:
                        # Darker gray - more opaque
                        alpha = int(150 + (threshold - brightness) / threshold * 105)
                        alpha = max(150, min(255, alpha))
                    new_data.append((watermark_gray, watermark_gray, watermark_gray, alpha))
                elif brightness >= threshold:
                    # Pure white/very bright colored background -> transparent
                    new_data.append((r, g, b, 0))
                else:
                    # Content or darker colored areas -> keep opaque
                    new_data.append((r, g, b, 255))
            else:
                # Original behavior: remove bright pixels
                if brightness > threshold:
                    new_data.append((r, g, b, 0))  # Transparent
                else:
                    new_data.append((r, g, b, 255))  # Opaque
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    return img


def process_image(input_path, output_path, method='color', threshold=240, edge_threshold=10, preserve_watermark=True):
    """
    Process a single image to remove background.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        method: 'color' or 'brightness'
        threshold: Brightness threshold
        edge_threshold: Edge detection threshold for color method
        preserve_watermark: If True, preserves watermarks during background removal
    """
    try:
        if method == 'color':
            img = remove_background_color_based(input_path, threshold, edge_threshold, preserve_watermark)
        else:
            img = remove_background_brightness_based(input_path, threshold, preserve_watermark)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as PNG with transparency
        img.save(output_path, 'PNG')
        print(f"  ✓ Processed: {input_path} -> {output_path}")
        return True
    except Exception as e:
        print(f"  ✗ Error processing {input_path}: {e}")
        return False


def process_directory(directory, output_dir=None, method='color', threshold=240, edge_threshold=10, 
                     recursive=True, supported_formats=None, preserve_watermark=True):
    """
    Process all images in a directory and subdirectories.
    
    Args:
        directory: Input directory path
        output_dir: Output directory path (default: same as input with '_transparent' suffix)
        method: 'color' or 'brightness'
        threshold: Brightness threshold
        edge_threshold: Edge detection threshold
        recursive: Process subdirectories
        supported_formats: List of supported image formats (default: common formats)
        preserve_watermark: If True, preserves watermarks during background removal
    """
    if supported_formats is None:
        supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']
    
    directory = Path(directory)
    
    if output_dir is None:
        output_dir = directory.parent / f"{directory.name}_transparent"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing images in: {directory}")
    print(f"Output directory: {output_dir}")
    print(f"Method: {method}, Threshold: {threshold}")
    print("-" * 60)
    
    processed = 0
    failed = 0
    
    # Find all image files
    if recursive:
        image_files = []
        for ext in supported_formats:
            image_files.extend(directory.rglob(f"*{ext}"))
            image_files.extend(directory.rglob(f"*{ext.upper()}"))
    else:
        image_files = []
        for ext in supported_formats:
            image_files.extend(directory.glob(f"*{ext}"))
            image_files.extend(directory.glob(f"*{ext.upper()}"))
    
    for img_path in image_files:
        # Calculate relative path for output
        rel_path = img_path.relative_to(directory)
        output_path = output_dir / rel_path.with_suffix('.png')
        
        if process_image(img_path, output_path, method, threshold, edge_threshold, preserve_watermark):
            processed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"✓ Processed: {processed} images")
    if failed > 0:
        print(f"✗ Failed: {failed} images")
    print(f"Output saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description='Remove backgrounds from images in a directory',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process images/background directory with color-based method
  python remove_backgrounds.py images/background
  
  # Use brightness-based method with custom threshold
  python remove_backgrounds.py images/background --method brightness --threshold 200
  
  # Process with custom output directory
  python remove_backgrounds.py images/background --output images/background_transparent
        """
    )
    
    parser.add_argument('directory', help='Directory containing images to process')
    parser.add_argument('-o', '--output', help='Output directory (default: input_dir_transparent)')
    parser.add_argument('-m', '--method', choices=['color', 'brightness'], default='color',
                       help='Background removal method (default: color)')
    parser.add_argument('-t', '--threshold', type=int, default=240,
                       help='Brightness threshold 0-255 (default: 240)')
    parser.add_argument('-e', '--edge-threshold', type=int, default=10,
                       help='Edge detection threshold for color method (default: 10)')
    parser.add_argument('--no-recursive', action='store_true',
                       help='Do not process subdirectories')
    parser.add_argument('--no-watermark', action='store_true',
                       help='Do not preserve watermarks (default: preserves watermarks)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        return 1
    
    process_directory(
        args.directory,
        args.output,
        args.method,
        args.threshold,
        args.edge_threshold,
        recursive=not args.no_recursive,
        preserve_watermark=not args.no_watermark
    )
    
    return 0


if __name__ == '__main__':
    exit(main())
