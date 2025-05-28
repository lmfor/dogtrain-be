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

@user_router.post("/", response_model=UserCreate, status_code=201) # Created -> Code 201
def create_user(payload: UserIn, db : Session=Depends(get_db)):
    
    if db.query(UserORM).filter_by(username=payload.username).first():
        raise HTTPException(409, "Username already taken!")
    
    user = UserORM(
        username=payload.username
        
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@user_router.get("/{token}", response_model=UserOut)
def get_user_info(token: UUIDType, db : Session=Depends(get_db)):
    user = db.query(UserORM).filter_by(token=token).first()
    if not user:
        raise HTTPException(404, "User not found!")
    return user

# We don't want an update method. Usernames are final.

@user_router.delete("/{token}", response_model=UserOut)
def delete_user_info(token: UUIDType, db : Session=Depends(get_db)):
    user = db.query(UserORM).filter_by(token=token).first()
    if not user:
        raise HTTPException(404, "User not found!")
    db.delete(user)
    db.commit()
    return user

app.include_router(user_router)




