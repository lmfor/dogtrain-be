from fastapi import FastAPI, Depends, Header, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from uuid import UUID as UUIDType
from models import User as UserORM
from schemas import *





origins = [
"http://localhost:8000"
          ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine) # create tables if they do not exist
    yield # will pause here until the app is shutdown 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1) Reads the `Authorization: Bearer <token>` header
# 2) Validates the token format
# 3) Looks up the `User` by that token
# 4) Raises a 401 if anything is wrong
def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db)
) -> UserORM:
    scheme, _, token_str = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(401, "Invalid auth scheme, use 'Bearer <token>'")
    try:
        token = UUIDType(token_str)
    except ValueError:
        raise HTTPException(401, "Malformed token")
    
    user = db.query(UserORM).filter_by(token=token).first()
    if not user:
        raise HTTPException(401, "Invalid or expired token")
    return user


app = FastAPI(lifespan=lifespan,
              title="Dog Training API",
              openapi_tags=[
                      {
                      "name":"Users",
                      "description":"Create, read, and delete users."
                      },
                      {
                      "name":"Dogs",
                      "description":"Create, read, update, and delete dog profiles!" 
                      }
              ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tag the following methods with 'Users'
user_router = APIRouter(prefix="/api/users", tags=["Users"])

# =======================================UNPROTECTED=======================================

#SIGN-UP
@user_router.post("/createaccount", response_model=UserCreate, status_code=201)
def create_user(payload: UserIn, db: Session = Depends(get_db)):
    if db.query(UserORM).filter_by(username=payload.username).first():
        raise HTTPException(409, "Username already taken!")
    
    user = UserORM(username=payload.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

#VIEW PROFILE
@user_router.get("/profile/{username}")
def view_public_profile(username:str, db: Session = Depends(get_db)):
    user = db.query(UserORM).filter_by(username=username).first()
    if not user:
        raise HTTPException(404, "User not found!")
    return user

# =======================================PROTECTED=======================================

# LOGIN LOGIC
@user_router.post("/login", response_model=UserCreate)
def login_user(
    payload: UserORM = Depends(get_current_user),
    db: Session = Depends(get_db)):
    user = db.query(UserORM).filter_by(username=payload.username).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user

@user_router.get("/me", response_model=UserOut)
def get_user_info(current_user: UserORM = Depends(get_current_user)):
    return current_user

# We don't want an update method. Usernames are final.

@user_router.delete("/me", response_model=UserOut)
def delete_user_info(
    current_user: UserORM = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.delete(current_user)
    db.commit()
    return current_user

app.include_router(user_router)

# Dog Router
dog_router = APIRouter(prefix="/api/dogs", tags=["Dogs"])



