import asyncio
from fastapi import FastAPI, Depends, Header, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from uuid import UUID
from alembic import command
from alembic.config import Config
import asyncio
from database import Base, engine, SessionLocal
import models
import schemas
from typing import List, Optional

# Allow both backend and frontend ports for local development
origins = [
    "http://localhost:8000",
    "http://localhost:5173",  # Default Vite dev server port
    "http://127.0.0.1:5173",
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # migrating any tables to latest revision
    def run_migrations():
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
    
    await asyncio.to_thread(run_migrations)
    # ensure tables exist for any models without migrations
    # Base.metadata.create_all(bind=engine)
    yield

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db)
) -> models.User:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    scheme, _, token_str = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication scheme; use 'Bearer <token>'"
        )
    
    try:
        token = UUID(token_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed token")
    
    user = db.query(models.User).filter(models.User.token == token).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

app = FastAPI(
    lifespan=lifespan,
    title="API WIP",
    openapi_tags=[
        {"name": "Users", "description": "Sign up, log in, view & delete your account."},
        {"name": "Dogs",  "description": "CRUD for dog profiles."},
        {"name": "Trainers", "description": "Endpoints for trainer locations."}
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
    summary="View someone's public profile"
)
def view_public_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found!")
    return {"id": user.id, "username": user.username}

app.include_router(user_router)


# ──────────────────────────────────────────────────────── TRAINERS ────────────────────────────────────────────────────────
trainer_router = APIRouter(prefix="/api/trainer", tags=["Trainers"])

@trainer_router.get(
    "/locations",
    response_model=List[schemas.LocationOut],
    summary="Get all trainer locations"
)
def get_trainer_locations(db: Session = Depends(get_db)):
    locations = db.query(models.TrainerLocation).all()
    return locations

@trainer_router.post(
    "/locations",
    response_model=schemas.LocationOut,
    status_code=201,
    summary="Create a new trainer location"
)
def create_trainer_location(
    location: schemas.LocationCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "trainer":
        raise HTTPException(status_code=403, detail="Only trainers can create locations")
    
    new_location = models.TrainerLocation(**location.model_dump(), trainer_id=current_user.id)
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

@trainer_router.put(
    "/locations/{location_id}",
    response_model=schemas.LocationOut,
    summary="Update a trainer location"
)
def update_trainer_location(
    location_id: UUID,
    location_update: schemas.LocationUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = db.query(models.TrainerLocation).filter(models.TrainerLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if location.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this location")
    
    for field, value in location_update.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    return location

@trainer_router.delete(
    "/locations/{location_id}",
    status_code=204,
    summary="Delete a trainer location"
)
def delete_trainer_location(
    location_id: UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    location = db.query(models.TrainerLocation).filter(models.TrainerLocation.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if location.trainer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this location")
    
    db.delete(location)
    db.commit()

app.include_router(trainer_router)


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

@dog_router.get(
    "/user/{user_id}",
    response_model=list[schemas.DogOut],
    summary="Fetch all dogs belonging to a user"
)
def get_user_dogs(user_id: UUID, db: Session = Depends(get_db)):
    dogs = db.query(models.Dog).filter(models.Dog.owner_id == user_id).all()
    return dogs

app.include_router(dog_router)
