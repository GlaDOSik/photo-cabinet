#!/usr/bin/env python3
"""
Generate test images with dates and numbers.
Each image contains a date (starting from 1. 1. 2026) and a number (starting from 99).
"""
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Output folder path - change this to your desired location
OUTPUT_FOLDER = "/home/ludek/ProjectData/PhotoCabinet/collection/Mix/testdata"

# Number of images to generate
NUM_IMAGES = 200


def generate_image(output_path: Path, date_str: str, number: int, image_size: int = 1000):
    """Generate a single image with white background and centered text."""
    # Create white background
    img = Image.new('RGB', (image_size, image_size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a larger font, fallback to default if not available
    try:
        # Try to use a system font - adjust path if needed for your system
        font_size = 120
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    
    # Prepare text lines
    line1 = date_str
    line2 = str(number)
    
    # Calculate text positions for centering
    # Get text bounding boxes
    bbox1 = draw.textbbox((0, 0), line1, font=font)
    bbox2 = draw.textbbox((0, 0), line2, font=font)
    
    text1_width = bbox1[2] - bbox1[0]
    text1_height = bbox1[3] - bbox1[1]
    text2_width = bbox2[2] - bbox2[0]
    text2_height = bbox2[3] - bbox2[1]
    
    # Calculate total height and spacing
    line_spacing = 20
    total_height = text1_height + line_spacing + text2_height
    
    # Center vertically and horizontally
    y_start = (image_size - total_height) // 2
    x1 = (image_size - text1_width) // 2
    y1 = y_start
    x2 = (image_size - text2_width) // 2
    y2 = y_start + text1_height + line_spacing
    
    # Draw text (black on white)
    draw.text((x1, y1), line1, fill='black', font=font)
    draw.text((x2, y2), line2, fill='black', font=font)
    
    # Save image
    img.save(output_path, 'JPEG', quality=95)


def set_exif_datetime(file_path: Path, date: datetime):
    """Set EXIF DateTimeOriginal using exiftool."""
    # Format: YYYY:MM:DD HH:MM:SS
    datetime_str = date.strftime("%Y:%m:%d %H:%M:%S")
    cmd = [
        'exiftool',
        '-overwrite_original',
        f'-EXIF:DateTimeOriginal={datetime_str}',
        str(file_path)
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to set EXIF data for {file_path}: {e.stderr.decode()}")


def main():
    output_folder = Path(OUTPUT_FOLDER)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Start date: 1. 1. 2026
    start_date = datetime(2026, 1, 1)
    
    # Calculate number of digits needed for zero-padding
    num_digits = len(str(NUM_IMAGES))
    
    # Generate images
    for i in range(NUM_IMAGES):
        number = NUM_IMAGES - i  # NUM_IMAGES, NUM_IMAGES-1, ..., 1
        current_date = start_date + timedelta(days=i)
        # Format: d. m. yyyy (without leading zeros)
        day = str(current_date.day)
        month = str(current_date.month)
        year = str(current_date.year)
        date_str = f"{day}. {month}. {year}"
        
        # Filename is the number with zero-padding for alphabetical sorting
        filename = f"{number:0{num_digits}d}.jpg"
        output_path = output_folder / filename
        
        print(f"Generating {filename} with date {date_str}...")
        generate_image(output_path, date_str, number)
        
        # Set EXIF DateTimeOriginal
        set_exif_datetime(output_path, current_date)
    
    print(f"\nGenerated {NUM_IMAGES} images in {output_folder}")


if __name__ == '__main__':
    main()

