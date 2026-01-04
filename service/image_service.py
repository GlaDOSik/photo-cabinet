import os

from PIL import Image
# import numpy as np
from collections import Counter

from dbe.photo import Photo
import pc_configuration
from vial.config import app_config


def get_image_size(photo_path: str) -> tuple[int, int]:
    """Get image dimensions (width, height) using Pillow.
    
    Args:
        photo_path: Path to the image file
    
    Returns:
        Tuple of (width, height) in pixels
    """
    with Image.open(photo_path) as img:
        return img.size  # Returns (width, height)


def generate_thumbnail(photo_path: str, thumbnail_name: str, target_path: str, size: int) -> str:
    """Generate a thumbnail of a photo.
    
    Args:
        photo_path: Full path to the photo
        thumbnail_name: name of the generated thumbnail
        target_path: Path to folder where thumbnail will be generated
        size: Largest dimension size (width or height, whichever is larger)
    
    Returns:
        Path to the generated thumbnail file
    """
    # Get source image path
    source_path = photo_path
    
    # Generate thumbnail filename using Photo.id
    thumbnail_filename = f"{thumbnail_name}.jpg"
    thumbnail_path = os.path.join(target_path, thumbnail_filename)
    
    # Open and process image
    with Image.open(source_path) as img:
        # Convert to RGB if necessary (handles RGBA, LA, P, etc.)
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            img = rgb_img
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # Create thumbnail (max_size ensures largest dimension is <= size, maintaining aspect ratio)
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        # Save thumbnail
        img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
    
    return thumbnail_path


# def get_dominant_color_kmeans(photo_path: str, k: int = 3, sample_size: int = 10000) -> str:
#     """Extract dominant color using K-means clustering (Method A).
#
#     Args:
#         photo_path: Path to the image file
#         k: Number of clusters (3-5 works well)
#         sample_size: Number of pixels to sample (faster processing)
#
#     Returns:
#         Hex color string (e.g., "#FF5733")
#     """
#     try:
#         from sklearn.cluster import KMeans
#     except ImportError:
#         raise ImportError("scikit-learn is required for get_dominant_color_kmeans. Install it with: pip install scikit-learn")
#
#     with Image.open(photo_path) as img:
#         # Convert to RGB
#         img = img.convert('RGB')
#
#         # Resize for faster processing
#         img.thumbnail((200, 200), Image.Resampling.LANCZOS)
#
#         # Get pixels as numpy array
#         pixels = np.array(img).reshape(-1, 3)
#
#         # Sample if too many pixels
#         if len(pixels) > sample_size:
#             pixels = pixels[np.random.choice(len(pixels), sample_size, replace=False)]
#
#         # K-means clustering
#         kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
#         kmeans.fit(pixels)
#
#         # Get the largest cluster (most common color)
#         labels = kmeans.labels_
#         cluster_sizes = np.bincount(labels)
#         dominant_cluster = np.argmax(cluster_sizes)
#         dominant_color = kmeans.cluster_centers_[dominant_cluster]
#
#         # Convert to RGB integers and format as hex
#         r, g, b = map(int, dominant_color)
#         return f"#{r:02x}{g:02x}{b:02x}"
#     except Exception as e:
#         raise RuntimeError(f"Error processing image for dominant color (K-means): {str(e)}")


def get_dominant_color_quantize(photo_path: str, colors: int = 256) -> str:
    """Extract dominant color by quantizing to palette (Method B).
    
    Args:
        photo_path: Path to the image file
        colors: Number of colors in quantized palette
    
    Returns:
        Hex color string (e.g., "#FF5733")
    """
    with Image.open(photo_path) as img:
        # Convert to RGB
        img = img.convert('RGB')
        
        # Resize for performance
        img.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        # Quantize to reduce color space
        quantized = img.quantize(colors=colors)
        
        # Get color palette
        palette = quantized.getpalette()
        
        # Count pixel colors
        pixels = list(quantized.getdata())
        most_common_color_index = Counter(pixels).most_common(1)[0][0]
        
        # Get RGB from palette (palette is [r1, g1, b1, r2, g2, b2, ...])
        r = palette[most_common_color_index * 3]
        g = palette[most_common_color_index * 3 + 1]
        b = palette[most_common_color_index * 3 + 2]
        
        # Format as hex
        return f"#{r:02x}{g:02x}{b:02x}"
