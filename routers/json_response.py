import datetime

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def dt_encoder(dt: datetime.datetime) -> str:
    return dt.isoformat(timespec="microseconds")


def json_response(
    obj: dict, status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(
            obj,
            custom_encoder={
                datetime.datetime: dt_encoder
            }
        ),
        status_code=status_code
    )
