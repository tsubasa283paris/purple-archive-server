from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from auth.auth import auth_router
from routers import users, albums


# app = FastAPI(dependencies=[Depends(get_query_token)])
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def handler(request: Request, exc: RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


app.include_router(auth_router)
app.include_router(users.router)
app.include_router(albums.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}