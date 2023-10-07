from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from auth.auth import auth_router
from dotenv import load_dotenv
from routers import users, albums, bookmarks, tags, gamemodes
from routers.temp_albums_cleaner import TempAlbumsCleaner


# load .env
load_dotenv()

app = FastAPI()

# exception handler to dump what's wrong
@app.exception_handler(RequestValidationError)
async def handler(request: Request, exc: RequestValidationError):
    print(exc)
    return JSONResponse(
        content={},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

app.include_router(auth_router)
app.include_router(users.router)
app.include_router(albums.router)
app.include_router(bookmarks.router)
app.include_router(tags.router)
app.include_router(gamemodes.router)

# kick temp_albums cleaner
temp_albums_cleaner = TempAlbumsCleaner()

@app.on_event("shutdown")
async def shutdown_event():
    global temp_albums_cleaner
    temp_albums_cleaner.stop()
