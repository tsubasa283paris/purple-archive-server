import datetime
from typing import Union

from jose import JWTError, jwt


JWT_KEY = "thisisdummy"
JWT_ALGORITHM = "HS256"


def encode_access_token(
    username: str,
    expires_delta: Union[datetime.timedelta, None] = None
):
    expire = datetime.datetime.utcnow()
    if expires_delta:
        expire += expires_delta
    else:
        expire += datetime.timedelta(minutes=15)
    return jwt.encode(
        {
            "sub": username,
            "exp": expire,
        },
        JWT_KEY,
        algorithm=JWT_ALGORITHM
    )


def decode_access_token(
    token: str
) -> Union[str, None]:
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub")
