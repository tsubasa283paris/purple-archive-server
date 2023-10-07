import datetime

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def dt_encoder(dt: datetime.datetime) -> str:
    return dt.isoformat(timespec="microseconds")


def json_response(obj: dict) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(
            obj,
            custom_encoder={
                datetime.datetime: dt_encoder
            }
        )
    )
