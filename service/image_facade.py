from dbe.photo import Photo
from service import image_service
import pc_configuration
from vial.config import app_config

def generate_thumbnail(photo: Photo, thumbnail_size: int):
    # Get the main generated folder path
    generated_path = app_config.get_configuration(pc_configuration.GENERATED_PATH)
    image_service.generate_thumbnail(photo.get_photo_file_path(), str(photo.id), generated_path, thumbnail_size)
    photo.metadata_index.use_thumbnail = True

def get_dominant_color_quantize(photo: Photo) -> str:
    return image_service.get_dominant_color_quantize(photo.get_photo_file_path())