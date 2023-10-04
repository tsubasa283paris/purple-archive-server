from dataclasses import dataclass
from io import BytesIO
from typing import List

from google.cloud.vision import ImageAnnotatorClient
from google.cloud.vision_v1.types import Feature
from google.oauth2 import service_account
from PIL import Image


GAPI_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"
GAPI_CRED_FILE = "google_api_credentials.json"

AREA_BOUND_SUBT = ((95, 143), (673, 393))
AREA_BOUND_PLAYER = ((21, 461), (627, 496))

DEFAULT_LANG_HINT = "ja"


@dataclass
class ImageAnnotation:
    description: str
    player_name: str


def annotate_images(
    images: List[Image.Image], lang_hint: str = DEFAULT_LANG_HINT
) -> List[ImageAnnotation]:
    # load credentials
    credentials = service_account.Credentials \
        .from_service_account_file(GAPI_CRED_FILE)
    
    # prepare client
    client = ImageAnnotatorClient(credentials=credentials)

    # create request object formatted for Google Vision API
    gapi_request_param: List[dict] = []
    for image in images:
        buffer = BytesIO()
        image.convert("RGB").save(buffer, "jpeg")
        gapi_request_param.append({
            "image": {
                "content": buffer.getvalue()
            },
            "features": [{
                "type_": Feature.Type.DOCUMENT_TEXT_DETECTION
            }],
            "image_context": {
                "language_hints": lang_hint
            }
        })

    # call API
    response = client.batch_annotate_images(requests=gapi_request_param)

    # filter results to format into ImageAnnotation
    result: List[ImageAnnotation] = []
    for air in response.responses:
        subt_str = ""
        player_str = ""
        for text in air.text_annotations:
            vertices = text.bounding_poly.vertices
            if len(vertices) != 4:
                continue

            if vertices[0].x > AREA_BOUND_SUBT[0][0] and \
                vertices[0].y > AREA_BOUND_SUBT[0][1] and \
                vertices[2].x < AREA_BOUND_SUBT[1][0] and \
                vertices[2].y < AREA_BOUND_SUBT[1][1]:
                subt_str += text.description
            elif vertices[0].x > AREA_BOUND_PLAYER[0][0] and \
                vertices[0].y > AREA_BOUND_PLAYER[0][1] and \
                vertices[2].x < AREA_BOUND_PLAYER[1][0] and \
                vertices[2].y < AREA_BOUND_PLAYER[1][1]:
                player_str = text.description
        
        result.append(ImageAnnotation(subt_str, player_str))
    
    return result
