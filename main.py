import datetime
from fastapi import FastAPI, status, Response, Depends, HTTPException
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
import os


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/rider_db")

app = FastAPI(
    title="Rider Service"
)
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class RiderModel(Base):
    __tablename__ = "riders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

class RiderBase(BaseModel):
    name: str
    email: str
    phone_number: str

class RiderCreate(RiderBase):
    pass

class RiderUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone_number: str | None = None


class Rider(RiderBase):
    id: int
    created_at: datetime.datetime
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_rider(db: Session, rider: RiderCreate):
    db_rider = RiderModel(name=rider.name, email=rider.email, phone_number=rider.phone_number)
    db.add(db_rider)
    db.commit()
    db.refresh(db_rider)
    return db_rider

def get_rider(db: Session, rider_id: int):
    db_rider = db.query(RiderModel).filter(RiderModel.id == rider_id).first()
    if db_rider is None:
        raise HTTPException(status_code=404, detail="Rider not found")
    return db_rider

def get_riders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(RiderModel).offset(skip).limit(limit).all()

def update_rider(db: Session, rider_id: int, rider_update: RiderUpdate):
    db_rider = db.query(RiderModel).filter(RiderModel.id == rider_id).first()
    if not db_rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    if rider_update.name is not None:
        db_rider.name = rider_update.name
    if rider_update.email is not None:
        db_rider.email = rider_update.email
    if rider_update.phone_number is not None:
        db_rider.phone_number = rider_update.phone_number

    db.commit()
    db.refresh(db_rider)
    return db_rider

def remove_rider(db: Session, rider_id: int):
    db_rider = db.query(RiderModel).filter(RiderModel.id == rider_id).first()
    if not db_rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    db.delete(db_rider)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.post("/v1/riders", response_model=Rider, status_code=status.HTTP_201_CREATED)
def create_rider_endpoint(rider: RiderCreate, db: Session = Depends(get_db)):
    return create_rider(db=db, rider=rider)

@app.get("/v1/riders/{rider_id}", response_model=Rider)
def get_rider_endpoint(rider_id: int, db: Session = Depends(get_db)):
    return get_rider(db=db, rider_id=rider_id)

@app.get("/v1/riders", response_model=list[Rider])
def get_riders_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_riders(db=db, skip=skip, limit=limit)

@app.patch("/v1/riders/{id}", response_model=Rider, status_code=status.HTTP_200_OK)
def update_rider_endpoint(rider_id: int, rider_update: RiderUpdate, db: Session = Depends(get_db)):
    return update_rider(db=db, rider_id=rider_id, rider_update=rider_update)

@app.delete("/v1/riders/{id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_rider_endpoint(rider_id: int, db: Session = Depends(get_db)):
    return remove_rider(db=db, rider_id=rider_id)