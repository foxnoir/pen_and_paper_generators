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


def remove_background_color_based(image_path, threshold=200, edge_threshold=25, preserve_watermark=True):
    """
    Removes background based on color similarity to edges.
    Samples edge pixels to determine background color more accurately.
    More aggressive background removal while preserving actual content.
    
    Args:
        image_path: Path to the image file
        threshold: Brightness threshold for background removal (0-255, lower = more aggressive)
        edge_threshold: Threshold for color distance detection (higher = more aggressive)
        preserve_watermark: If True, preserves darker pixels that might be watermarks
    
    Returns:
        PIL Image with transparent background
    """
    img = Image.open(image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Sample edge pixels more comprehensively to determine background color
    width, height = img.size
    edge_pixels = []
    
    # Sample more edge pixels (not just corners)
    sample_step = max(1, min(width, height) // 20)  # Sample every 5% of edge
    
    # Top and bottom edges
    for x in range(0, width, sample_step):
        edge_pixels.append(img.getpixel((x, 0)))  # Top
        edge_pixels.append(img.getpixel((x, height-1)))  # Bottom
    
    # Left and right edges
    for y in range(0, height, sample_step):
        edge_pixels.append(img.getpixel((0, y)))  # Left
        edge_pixels.append(img.getpixel((width-1, y)))  # Right
    
    # Calculate average background color from edge pixels
    valid_pixels = [p for p in edge_pixels if len(p) >= 3]
    if not valid_pixels:
        valid_pixels = [(255, 255, 255)]  # Fallback to white
    
    avg_r = sum(c[0] for c in valid_pixels) // len(valid_pixels)
    avg_g = sum(c[1] for c in valid_pixels) // len(valid_pixels)
    avg_b = sum(c[2] for c in valid_pixels) // len(valid_pixels)
    
    # Calculate average brightness of edge pixels
    edge_brightness = sum((c[0] + c[1] + c[2]) / 3 for c in valid_pixels) / len(valid_pixels)
    
    # Create new image with transparency
    data = img.getdata()
    new_data = []
    
    # Only preserve grayscale pixels that are actually dark (content), not light backgrounds
    watermark_brightness_threshold = threshold - 30  # Only preserve grayscale darker than this
    
    for item in data:
        if len(item) >= 3:
            r, g, b = item[0], item[1], item[2]
            a = item[3] if len(item) > 3 else 255
            
            # Calculate distance from background color
            color_distance = ((r - avg_r)**2 + (g - avg_g)**2 + (b - avg_b)**2)**0.5
            
            # Calculate brightness
            brightness = (r + g + b) / 3
            
            # Check if pixel is grayscale (moderate threshold)
            grayscale_threshold = 30
            is_grayscale = abs(r - g) < grayscale_threshold and abs(g - b) < grayscale_threshold and abs(r - b) < grayscale_threshold
            
            if preserve_watermark:
                # CRITICAL: Always preserve very dark pixels (black lines, text, etc.)
                # These are definitely content, not background
                dark_content_threshold = 80  # Pixels darker than this are always content
                if brightness < dark_content_threshold:
                    # Very dark pixel - definitely content (lines, text, etc.) - always preserve
                    new_data.append((r, g, b, 255))
                # CRITICAL: Preserve ALL grayscale pixels that are not too bright
                # This includes light gray table lines (brightness ~150-220)
                # Only remove very bright grayscale (almost white, brightness > 240)
                elif is_grayscale:
                    # Grayscale pixel - could be table lines, text, or content
                    # Preserve all grayscale except very bright ones (almost white)
                    if brightness < 240:
                        # Convert grayscale content to black for better visibility
                        # This makes table lines clearly visible
                        if brightness < 150:
                            # Dark to medium gray - keep as is (already dark enough)
                            new_data.append((r, g, b, 255))
                        elif brightness < 220:
                            # Light gray (table lines) - convert to black
                            new_data.append((0, 0, 0, 255))
                        else:
                            # Very light gray - convert to black but slightly less opaque
                            new_data.append((0, 0, 0, 240))
                    else:
                        # Very bright grayscale (almost white) - remove as background
                        new_data.append((r, g, b, 0))
                elif color_distance < edge_threshold or brightness > threshold:
                    # Background color -> transparent
                    new_data.append((r, g, b, 0))
                else:
                    # Keep pixel with original alpha (likely content)
                    new_data.append((r, g, b, a))
            else:
                # More aggressive: remove anything close to background color or bright
                # BUT always preserve very dark pixels and grayscale content (table lines, etc.)
                dark_content_threshold = 80
                if brightness < dark_content_threshold:
                    # Very dark pixel - always preserve
                    new_data.append((r, g, b, 255))
                elif is_grayscale and brightness < 240:
                    # Convert grayscale content to black for better visibility
                    if brightness < 150:
                        # Dark to medium gray - keep as is
                        new_data.append((r, g, b, 255))
                    elif brightness < 220:
                        # Light gray (table lines) - convert to black
                        new_data.append((0, 0, 0, 255))
                    else:
                        # Very light gray - convert to black
                        new_data.append((0, 0, 0, 240))
                elif color_distance < edge_threshold or brightness > threshold:
                    new_data.append((r, g, b, 0))
                else:
                    new_data.append((r, g, b, a))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    return img


def remove_background_brightness_based(image_path, threshold=200, preserve_watermark=True):
    """
    Removes background based on brightness threshold.
    More aggressive background removal while preserving actual content.
    
    Args:
        image_path: Path to the image file
        threshold: Brightness threshold (0-255, lower = more aggressive)
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
    
    # Only preserve dark grayscale pixels as content, not light backgrounds
    grayscale_threshold = 30
    watermark_brightness_threshold = threshold - 30  # Only preserve grayscale darker than this
    
    for i, item in enumerate(data):
        if len(item) >= 3:
            r, g, b = item[0], item[1], item[2]
            brightness = (r + g + b) / 3
            
            # Check if pixel is grayscale
            is_grayscale = abs(r - g) < grayscale_threshold and abs(g - b) < grayscale_threshold and abs(r - b) < grayscale_threshold
            
            if preserve_watermark:
                # CRITICAL: Always preserve very dark pixels (black lines, text, etc.)
                # These are definitely content, not background
                dark_content_threshold = 80  # Pixels darker than this are always content
                if brightness < dark_content_threshold:
                    # Very dark pixel - definitely content (lines, text, etc.) - always preserve
                    new_data.append((r, g, b, 255))
                # CRITICAL: Preserve ALL grayscale pixels that are not too bright
                # This includes light gray table lines (brightness ~150-220)
                # Only remove very bright grayscale (almost white, brightness > 240)
                elif is_grayscale:
                    # Grayscale pixel - could be table lines, text, or content
                    # Preserve all grayscale except very bright ones (almost white)
                    if brightness < 240:
                        # Convert grayscale content to black for better visibility
                        # This makes table lines clearly visible
                        if brightness < 150:
                            # Dark to medium gray - keep as is (already dark enough)
                            new_data.append((r, g, b, 255))
                        elif brightness < 220:
                            # Light gray (table lines) - convert to black
                            new_data.append((0, 0, 0, 255))
                        else:
                            # Very light gray - convert to black but slightly less opaque
                            new_data.append((0, 0, 0, 240))
                    else:
                        # Very bright grayscale (almost white) - remove as background
                        new_data.append((r, g, b, 0))
                elif brightness >= threshold:
                    # Bright background -> transparent
                    new_data.append((r, g, b, 0))
                else:
                    # Content or darker colored areas -> keep opaque
                    new_data.append((r, g, b, 255))
            else:
                # More aggressive: remove bright pixels
                # BUT always preserve very dark pixels and grayscale content (table lines, etc.)
                dark_content_threshold = 80
                if brightness < dark_content_threshold:
                    # Very dark pixel - always preserve
                    new_data.append((r, g, b, 255))
                elif is_grayscale and brightness < 240:
                    # Convert grayscale content to black for better visibility
                    if brightness < 150:
                        # Dark to medium gray - keep as is
                        new_data.append((r, g, b, 255))
                    elif brightness < 220:
                        # Light gray (table lines) - convert to black
                        new_data.append((0, 0, 0, 255))
                    else:
                        # Very light gray - convert to black
                        new_data.append((0, 0, 0, 240))
                elif brightness > threshold:
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
    parser.add_argument('-t', '--threshold', type=int, default=200,
                       help='Brightness threshold 0-255 (default: 200, lower = more aggressive)')
    parser.add_argument('-e', '--edge-threshold', type=int, default=25,
                       help='Edge detection threshold for color method (default: 25, higher = more aggressive)')
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
