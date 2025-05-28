from fastapi import FastAPI, Depends, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import Base, engine, SessionLocal
from sqlalchemy.orm import Session
from schemas import TestCreateOut, TestCreateIn, TestReadOut
from models import TestClass as TestORM





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


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def get_root():
    return {"RESPONSE": "200 OK"}

# Test call
test = {"Test": "Response"}

@app.post("/api/", response_model=TestCreateOut)
def create_test(payload : TestCreateIn = Body(...), db: Session = Depends(get_db)):
    
    obj = TestORM(
        description=payload.description,
        tag=payload.tag
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/api/{id}", response_model=TestReadOut)
def read_test(id: int, db: Session = Depends(get_db)):
    obj = db.query(TestORM).filter(TestORM.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Error: Not found")
    return obj

@app.delete("/api/{id}", response_model=TestReadOut)
def delete_test(id: int, db: Session = Depends(get_db)):
    obj = db.query(TestORM).filter(TestORM.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Error: Not found")
    
    db.delete(obj)
    db.commit()
    return obj