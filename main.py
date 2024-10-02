from fastapi import FastAPI, Form, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, time
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Get environment variables
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
SECRET_KEY = os.getenv('SECRET_KEY')

# Configure Logging
logging.basicConfig(level=logging.INFO)

# FastAPI app setup
app = FastAPI()

# Configure session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# OAuth Configuration
config_data = {
    'GOOGLE_CLIENT_ID': CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': CLIENT_SECRET,
}
config = Config(environ=config_data)
oauth = OAuth(config)

# Register the Google OAuth
oauth.register(
    name='google',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
    redirect_uri='http://127.0.0.1:8000/auth',
)

# Allowed emails and domains
ALLOWED_EMAILS = [
    'sias.runclub@krea.edu.in',
    'sias.esok@krea.ac.in',
    'sias.finearts@krea.ac.in'
]
ALLOWED_DOMAINS = [
    'sias22@krea.ac.in',
]

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    user = request.session.get('user')
    if user:
        return f"<h1>Welcome {user['name']}</h1><a href='/logout'>Logout</a>"
    return "<a href='/login'><button>Login with Google</button></a>"
    

# Login route
@app.route('/login')
async def login(request: Request):
    redirect_uri = 'http://127.0.0.1:8000/auth'
    # Adding 'hd' parameter to restrict to specific hosted domain (e.g., krea.ac.in)
    return await oauth.google.authorize_redirect(request, redirect_uri, hd='krea.ac.in')

# Authentication callback route
@app.route('/auth')
async def auth(request: Request):
    try:
        # Retrieve the authorization token
        token = await oauth.google.authorize_access_token(request)
        if not token:
            logging.error("Failed to receive token from Google.")
            return HTMLResponse(content="Failed to receive token from Google", status_code=400)

        logging.info(f"Token received: {token}")

        # Use userinfo_endpoint to get user details
        user = await oauth.google.userinfo(token=token)
        if user:
            user_email = user['email']
            # Validate if email belongs to the allowed domain or specific allowed emails
            if (
                any(user_email.endswith(domain) for domain in ALLOWED_DOMAINS) or
                user_email in ALLOWED_EMAILS
            ):
                request.session['user'] = dict(user)  # Save user info in session
                return RedirectResponse(url='/bookings')
            else:
                logging.warning(f"Unauthorized email domain attempted login: {user_email}")
                return HTMLResponse(content="Unauthorized domain. Access restricted to specific domains or emails only.", status_code=403)

        else:
            logging.error("User info retrieval failed.")
            return HTMLResponse(content="Authentication failed: Could not retrieve user information.", status_code=400)

    except Exception as e:
        logging.error(f"Exception occurred during authentication: {e}")
        return HTMLResponse(content=f"Error during authentication: {str(e)}", status_code=500)

# Logout route
@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

# Bookings page route
@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/')
    
    return templates.TemplateResponse("booking_form.html", {"request": request, "user_email": user['email']})

# Booking creation route
@app.post("/bookings/")
def create_booking(
    club_name: str = Form(...),
    space_id: int = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
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