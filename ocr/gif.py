from typing import List

from PIL import Image


THUMB_SIZE = (250, 250)


class GifManager:
    src_path: str
    images: List[Image.Image]

    def __init__(self, gif_path: str) -> None:
        self.src_path = gif_path
        self.images = []

        with Image.open(gif_path) as image:
            for i in range(image.n_frames):
                image.seek(i)
                self.images.append(image.copy())
    
    def save_thumb(self, dst: str) -> None:
        thumb_images: List[Image.Image] = []
        for image in self.images:
            thumb_image = image.copy()
            thumb_image.thumbnail(THUMB_SIZE)
            thumb_images.append(thumb_image)

        thumb_images[0].save(
            dst,
            save_all=True,
            append_images=thumb_images[1:],
            loop=0,
        )
