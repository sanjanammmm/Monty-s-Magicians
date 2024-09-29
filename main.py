from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, time
from fastapi.staticfiles import StaticFiles

# Database setup
DATABASE_URL = "sqlite:///./club_bookings.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database models
class Club(Base):
    __tablename__ = "clubs"
    club_id = Column(Integer, primary_key=True, index=True)
    club_name = Column(String, unique=True, index=True)

class Space(Base):
    __tablename__ = "spaces"
    space_id = Column(Integer, primary_key=True, index=True)
    space_name = Column(String, unique=True, index=True)

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.club_id"))
    space_id = Column(Integer, ForeignKey("spaces.space_id"))
    booking_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)

    club = relationship("Club")
    space = relationship("Space")

Base.metadata.create_all(bind=engine)

# FastAPI app setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Main route
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("booking_form.html", {"request": request})

@app.post("/bookings/")
def create_booking(
    club_name: str = Form(...),
    space_id: int = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...)
):
    db = SessionLocal()
    try:
        # Get the club_id by club_name
        club = db.query(Club).filter(Club.club_name == club_name).first()
        if not club:
            raise HTTPException(status_code=400, detail="Club not found.")

        # Calculate end_time (1 hour after start_time)
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour = start_hour + 1 if start_hour < 23 else 0
        end_time = f"{end_hour:02d}:00"

        # Convert booking_date string to a date object
        booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()

        # Convert start_time and end_time strings to time objects
        start_time_obj = time(int(start_time.split(':')[0]), int(start_time.split(':')[1]))
        end_time_obj = time(int(end_time.split(':')[0]), int(end_time.split(':')[1]))

        # Check for existing bookings
        existing_booking = db.query(Booking).filter(
            Booking.space_id == space_id,
            Booking.booking_date == booking_date_obj,
            ((Booking.start_time <= start_time_obj) & (Booking.end_time > start_time_obj)) |
            ((Booking.start_time < end_time_obj) & (Booking.end_time >= end_time_obj)) |
            ((Booking.start_time >= start_time_obj) & (Booking.end_time <= end_time_obj))
        ).first()

        if existing_booking:
            raise HTTPException(status_code=400, detail="This time slot is already booked for the selected space.")

        new_booking = Booking(club_id=club.club_id, space_id=space_id, booking_date=booking_date_obj, start_time=start_time_obj, end_time=end_time_obj)
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return {"message": "Booking successful!", "booking_id": new_booking.booking_id}
    finally:
        db.close()

# run web app: uvicorn main:app --reload


