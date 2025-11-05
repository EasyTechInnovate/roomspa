import os
from django.conf import settings
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

imagekit_client = ImageKit(
    private_key=settings.IMAGEKIT_PRIVATE_KEY,
    public_key=settings.IMAGEKIT_PUBLIC_KEY,
    url_endpoint=settings.IMAGEKIT_URL_ENDPOINT
)

def upload_image(file_path, folder_path):
    try:
        with open(file_path, "rb") as f:
            result = imagekit_client.upload_file(
                file=f,
                file_name=os.path.basename(file_path),
                options=UploadFileRequestOptions(
                    folder=folder_path,
                    use_unique_file_name=True
                )
            )
        os.remove(file_path)
        return result.url
    except Exception as e:
        return None