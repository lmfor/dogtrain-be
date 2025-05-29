from fastapi import FastAPI, Depends, Header, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from uuid import UUID as UUIDType
from alembic import command
from alembic.config import Config
from database import Base, engine, SessionLocal
import models
import schemas

# Allow localhost for local testing
origins = ["http://localhost:8000"]

# Point alembic at my config file
##alembic_cfg = Config("alembic.ini")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # migrating any tables to latest revision
    #command.upgrade(alembic_cfg, "head")
    # ensure tables exist for any models without migrations
    Base.metadata.create_all(bind=engine)
    yield

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db)
) -> models.User:
    scheme, _, token_str = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme; use 'Bearer <token>'")
    try:
        token = UUIDType(token_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed token")
    user = db.query(models.User).filter(models.User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user

app = FastAPI(
    lifespan=lifespan,
    title="API WIP",
    openapi_tags=[
        {"name": "Users", "description": "Sign up, log in, view & delete your account."},
        {"name": "Dogs",  "description": "CRUD for dog profiles."}
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────── USERS ──────────────────────────────────────────────────────
user_router = APIRouter(prefix="/api/users", tags=["Users"])

@user_router.post(
    "/createaccount",
    response_model=schemas.UserOut,
    status_code=201,
    summary="Sign up with username + password"
)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already taken!")
    new_user = models.User(
        username=payload.username,
        hashed_password=models.User.hash_password(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@user_router.post(
    "/login",
    response_model=schemas.UserOut,
    summary="Log in with username + password to retrieve your token"
)
def login_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not user.verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@user_router.get(
    "/me",
    response_model=schemas.UserOut,
    summary="Get your own profile (requires Bearer token)"
)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@user_router.delete(
    "/me",
    response_model=schemas.UserOut,
    summary="Delete your account (requires Bearer token)"
)
def delete_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return current_user

# Public profile (no token) — only username & id
@user_router.get(
    "/profile/{username}",
    summary="View someone’s public profile"
)
def view_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    return {"id": user.id, "username": user.username}

app.include_router(user_router)


# ──────────────────────────────────────────────────────── DOGS ────────────────────────────────────────────────────────
dog_router = APIRouter(prefix="/api/dogs", tags=["Dogs"])

@dog_router.post(
    "/",
    response_model=schemas.DogOut,
    summary="Create a new dog profile"
)
def create_dog(dog_in: schemas.DogCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == dog_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found!")
    dog = models.Dog(**dog_in.model_dump())
    db.add(dog)
    db.commit()
    db.refresh(dog)
    return dog

@dog_router.get(
    "/{dog_id}",
    response_model=schemas.DogOut,
    summary="Fetch a single dog by ID"
)
def get_dog(dog_id: str, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog

@dog_router.patch(
    "/{dog_id}",
    response_model=schemas.DogOut,
    summary="Update fields of a dog profile"
)
def update_dog(dog_id: str, dog_up: schemas.DogUpdate, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    for field, val in dog_up.model_dump(exclude_unset=True, exclude_none=True).items():
        if val is not None:
            setattr(dog, field, val)
    db.commit()
    db.refresh(dog)
    return dog

@dog_router.delete(
    "/{dog_id}",
    status_code=204,
    summary="Delete a dog profile"
)
def delete_dog(dog_id: str, db: Session = Depends(get_db)):
    dog = db.query(models.Dog).filter(models.Dog.id == dog_id).first()
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    db.delete(dog)
    db.commit()

app.include_router(dog_router)
