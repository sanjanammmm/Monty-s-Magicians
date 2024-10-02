# FastAPI provides tools to define routes, request parameters, and handle different request methods.
from fastapi import FastAPI, Form, HTTPException, Request, Depends

# HTMLResponse and RedirectResponse are used to serve HTML content and handle redirections in the FastAPI application.
from fastapi.responses import HTMLResponse, RedirectResponse

# Jinja2Templates is used for server-side rendering of HTML templates to produce dynamic content based on user data.
from fastapi.templating import Jinja2Templates

# SQLAlchemy components for ORM (Object Relational Mapping) to facilitate interaction with the database without writing raw SQL queries.
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# datetime and time are used to manage and manipulate date and time objects for bookings.
from datetime import datetime, time

# StaticFiles serves static files (CSS)
from fastapi.staticfiles import StaticFiles

# Authlib integrates OAuth authentication, in this case, Google's OAuth, with the FastAPI application.
from authlib.integrations.starlette_client import OAuth

# Config from Starlette allows for easy management of environment configurations.
from starlette.config import Config

# SessionMiddleware is middleware to manage user sessions, allowing data persistence between different requests (login sessions).
from starlette.middleware.sessions import SessionMiddleware

# dotenv loads environment variables from a `.env` file for secure configuration.
from dotenv import load_dotenv

# os library to access the system's environment variables, which include OAuth keys and secret keys.
import os

# logging module is used for logging information, warnings, and error messages for better debugging and tracking application flow.
import logging

# Load environment variables from the .env file to manage credentials safely.
load_dotenv()

# Get environment variables related to Google OAuth and application security.
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')  
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET') 
SECRET_KEY = os.getenv('SECRET_KEY')  

# Configure logging settings to log information. This helps in debugging and tracking issues.
logging.basicConfig(level=logging.INFO)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files for the application, enabling serving of static content (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2Templates for server-side HTML rendering using templates stored in the "templates" directory.
templates = Jinja2Templates(directory="templates")

# OAuth configuration for integrating with Google, setting up credentials to authenticate with Google's OAuth service.
config_data = {
    'GOOGLE_CLIENT_ID': CLIENT_ID,
    'GOOGLE_CLIENT_SECRET': CLIENT_SECRET,
}
config = Config(environ=config_data)  
oauth = OAuth(config)  # Create an OAuth instance for managing authentication.

# Register Google OAuth with all necessary endpoints and configuration.
oauth.register(
    name='google',  
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET,  
    authorize_url='https://accounts.google.com/o/oauth2/auth',  # URL to authorize the user.
    access_token_url='https://accounts.google.com/o/oauth2/token',  # URL to obtain the access token.
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # URL to get user information.
    client_kwargs={'scope': 'openid email profile'},  
    redirect_uri='http://127.0.0.1:8000/auth', 
)

ALLOWED_EMAILS = [
    'sias.runclub@krea.edu.in',
    'sias.esok@krea.ac.in',
    'sias.finearts@krea.ac.in'
]
ALLOWED_DOMAINS = [
    'sias22@krea.ac.in',
]

# Define routes for the FastAPI application.

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """
    Renders the homepage of the application.
    If the user is logged in, it displays a welcome message.
    Otherwise, it displays a Google login button.
    
    Parameters:
    request (Request): The incoming HTTP request.

    Returns:
    HTMLResponse: Either a welcome message or a login button based on session status.
    """
    user = request.session.get('user')  # Get user information from the session.
    if user:
        return f"<h1>Welcome {user['name']}</h1><a href='/logout'>Logout</a>"  
    return "<a href='/login'><button>Login with Google</button></a>"  

@app.route('/login')
async def login(request: Request):
    """
    Initiate the OAuth login process using Google OAuth.
    Redirects the user to the Google login page for authentication.
    
    Parameters:
    request (Request): The incoming HTTP request.

    Returns:
    OAuth Redirect: Redirects to Google's OAuth service for authentication.
    """
    redirect_uri = 'http://127.0.0.1:8000/auth'  # Redirect URI after authentication.
    return await oauth.google.authorize_redirect(request, redirect_uri, hd='krea.ac.in')

@app.route('/auth')
async def auth(request: Request):
    """
    Handle the OAuth callback once the user is authenticated by Google.
    Retrieves user info and validates if they are authorized based on the allowed email or domain list.
    
    Parameters:
    request (Request): The incoming HTTP request.

    Returns:
    RedirectResponse or HTMLResponse: Redirects to booking page if authorized or shows error messages if not.
    """
    try:
        # Authorize the access token from the callback request.
        token = await oauth.google.authorize_access_token(request)
        if not token:
            logging.error("Failed to receive token from Google.")
            return HTMLResponse(content="Failed to receive token from Google", status_code=400)

        logging.info(f"Token received: {token}")
        user = await oauth.google.userinfo(token=token)  # Get user information.
        if user:
            user_email = user['email']
            # Check if the user's email is in the allowed domains or email list.
            if (
                any(user_email.endswith(domain) for domain in ALLOWED_DOMAINS) or
                user_email in ALLOWED_EMAILS
            ):
                request.session['user'] = dict(user)  # Save the user information in the session.
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

@app.route('/logout')
async def logout(request: Request):
    """
    Logs out the user by removing the user information from the session.
    
    Parameters:
    request (Request): The incoming HTTP request.

    Returns:
    RedirectResponse: Redirects to the homepage after logout.
    """
    request.session.pop('user', None)  # Remove user from the session.
    return RedirectResponse(url='/')

# Database setup
# Create the database engine and session.
DATABASE_URL = "sqlite:///./club_bookings.db"  
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models.
Base = declarative_base()

# Define database models for Clubs, Spaces, and Bookings.
class Club(Base):
    __tablename__ = "clubs"
    club_id = Column(Integer, primary_key=True, index=True)  # Unique identifier for each club.
    club_name = Column(String, unique=True, index=True)  # Name of the club, must be unique.

class Space(Base):
    __tablename__ = "spaces"
    space_id = Column(Integer, primary_key=True, index=True)  
    space_name = Column(String, unique=True, index=True)  

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True, index=True)  
    club_id = Column(Integer, ForeignKey("clubs.club_id"))  # Foreign key linking to a club.
    space_id = Column(Integer, ForeignKey("spaces.space_id"))  # Foreign key linking to a space.
    booking_date = Column(Date)  
    start_time = Column(Time)  
    end_time = Column(Time)  

    # Define relationships to access related Club and Space data.
    club = relationship("Club")
    space = relationship("Space")

# Create all the defined tables in the SQLite database.
Base.metadata.create_all(bind=engine)

# Utility functions 
def get_db():
    """
    Creates a new database session for each request, providing thread-safe access.
    
    Yields:
    db (Session): A database session for interacting with the database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_end_hour_from_start_hour(start_hour: int) -> int:
    """
    Calculate the end hour for a booking based on the start hour.
    If the start hour is 23 (11 PM), wraps around to 0 (12 AM) to signify the next day.

    Parameters:
    start_hour (int): The hour when the booking starts (in 24-hour format).

    Returns:
    int: The end hour for the booking.
    """
    return start_hour + 1 if start_hour < 23 else 0

def get_end_time_from_end_hour(end_hour: int) -> str:
    """
    Format the end hour as a time string in 'HH:00' format.

    Parameters:
    end_hour (int): The ending hour for the booking.

    Returns:
    str: Formatted time string for the ending hour.
    """
    return f"{end_hour:02d}:00"

def get_date_object_from_string(booking_date: str) -> datetime.date:
    """
    Convert a date string in 'YYYY-MM-DD' format to a datetime.date object.

    Parameters:
    booking_date (str): The date string representing the booking date.

    Returns:
    datetime.date: The parsed date object.
    """
    return datetime.strptime(booking_date, "%Y-%m-%d").date()

def get_time_object_from_string(time_string: str) -> time:
    """
    Convert a time string in 'HH:MM' format to a datetime.time object.

    Parameters:
    time_string (str): The time string to be converted.

    Returns:
    time: The parsed time object.
    """
    return time(int(time_string.split(':')[0]), int(time_string.split(':')[1]))

def verify_club_exists(club_name: str, db: Session):
    """
    Verify if a club exists in the database based on the given club name.
    Raises an HTTPException if the club is not found.

    Parameters:
    club_name (str): The name of the club to be verified.
    db (Session): The current database session.

    Returns:
    Club: The club object if found.
    """
    club = db.query(Club).filter(Club.club_name == club_name).first()
    if not club:
        raise HTTPException(status_code=400, detail="Club not found.")
    return club

def check_existing_booking(space_id: int, booking_date: datetime.date, start_time: time, end_time: time, db: Session):
    """
    Check if a booking already exists for a given space, date, and time slot combination.
    Ensures no overlapping bookings for the same space.

    Parameters:
    space_id (int): The identifier of the space being booked.
    booking_date (datetime.date): The date of the booking.
    start_time (time): The start time of the booking.
    end_time (time): The end time of the booking.
    db (Session): The current database session.

    Returns:
    Booking: The existing booking if found, otherwise None.
    """
    return db.query(Booking).filter(
        Booking.space_id == space_id,
        Booking.booking_date == booking_date,
        ((Booking.start_time <= start_time) & (Booking.end_time > start_time)) |
        ((Booking.start_time < end_time) & (Booking.end_time >= end_time)) |
        ((Booking.start_time >= start_time) & (Booking.end_time <= end_time))
    ).first()

@app.get("/bookings", response_class=HTMLResponse)
async def bookings_page(request: Request):
    """
    Render the booking form page where users can make reservations for club spaces.
    Requires the user to be logged in.

    Parameters:
    request (Request): The incoming HTTP request.

    Returns:
    HTMLResponse: The rendered booking form template.
    """
    user = request.session.get('user')  # Get user from session.
    if not user:
        return RedirectResponse(url='/')  # Redirect to homepage if not logged in.
    return templates.TemplateResponse("booking_form.html", {"request": request, "user_email": user['email']})

@app.post("/bookings/")
def create_booking(
    club_name: str = Form(...),
    space_id: int = Form(...),
    booking_date: str = Form(...),
    start_time: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Create a new booking for a club space, ensuring no overlapping bookings for the selected time and space.
    
    Parameters:
    club_name (str): Name of the club making the booking.
    space_id (int): ID of the space to be booked.
    booking_date (str): The date for the booking in 'YYYY-MM-DD' format.
    start_time (str): The start time for the booking in 'HH:MM' format.
    db (Session): The current database session (injected by FastAPI via Depends).

    Returns:
    dict: Success message and booking ID if the booking is created successfully.
    
    Raises:
    HTTPException: If the club is not found or the time slot is already booked.
    """
    # Verify if the club exists in the database.
    club = verify_club_exists(club_name, db)

    # Calculate the end time for the booking.
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour = get_end_hour_from_start_hour(start_hour)
    end_time = get_end_time_from_end_hour(end_hour)

    # Convert the date and time strings to datetime objects for storage.
    booking_date_obj = get_date_object_from_string(booking_date)
    start_time_obj = get_time_object_from_string(start_time)
    end_time_obj = get_time_object_from_string(end_time)

    # Check if a booking already exists for the selected space, date, and time slot.
    existing_booking = check_existing_booking(space_id, booking_date_obj, start_time_obj, end_time_obj, db)
    if existing_booking:
        raise HTTPException(status_code=400, detail="This time slot is already booked for the selected space.")

    # Create a new booking record in the database.
    new_booking = Booking(
        club_id=club.club_id,
        space_id=space_id,
        booking_date=booking_date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj
    )
    db.add(new_booking)  # Add the new booking to the session.
    db.commit()  # Commit the session to persist the changes.
    db.refresh(new_booking)  # Refresh the booking instance to get the latest state.
    return {"message": "Booking successful!", "booking_id": new_booking.booking_id}
