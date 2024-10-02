# Monty's Magicians: Clubs Event Booking Website
## Project Summary

1. **Introduction**: Within Krea University campus, numerous open-door events occur throughout the day and into the night, necessitating a streamlined space booking system for clubs.

2. **Related Work**: While many room booking systems exist (e.g., classroombookings, Roomzilla, Google Calendar), they often prioritize administration over user-friendliness and organize interfaces around events rather than users.

3. **Problem Statement**: There's a need for software that minimizes cognitive load for users during the booking process, focusing on ease of use for club representatives.

4. **Solution**: Our proposal ties each booking to a club's unique university email ID, ensuring transparency across the university regarding who booked a space, for how long, and for what purpose. This approach offers a centralized solution for improved information flow regarding space availability and occupancy.

5. **Validation**: Project completion can be validated when conflict-free room bookings are achievable, and booking information is clearly presented to the respective club representative.

## Available Spaces

The following spaces are available for booking:
- SH1, SH2, SH3
- 1A, 1B, 1C, 1D, 1E
- 2A, 2B, 2C, 2D, 2E, 2F, 2G
- 3A, 3B, 3C, 3D, 3E, 3F, 3G, 3H, 3I

## Features

- **User Restrictions**: Only clubs and societies can book spaces using this website.
- **Booking Details**: Club reps must provide club name, select space (from dropdown), select date (from dropdown), and choose a time slot (from dropdown).
- **Time Slots**: 1-hour slots available from 4 PM to 12 AM.
- **Conflict Prevention**: If a space is booked for a specific time slot, that slot will not be available for subsequent bookings of the same space.

## How to Run the Web App

To run the web app, use the following command in your terminal:

```
uvicorn main:app --reload
```

This command starts the FastAPI server with auto-reload enabled for development purposes.

## Project Artifacts

Our project utilizes the following key artifacts:

1. **Database Schema**: 
   - `club_bookings.db` containing tables for clubs, spaces, and bookings.
   - Implements relationships between entities to manage bookings effectively.

2. **FastAPI Application**: 
   - `main.py` containing the core application logic.
   - Handles routing, form processing, and database interactions.

3. **HTML Templates**:
   - Located in the `templates` directory.
   - Includes `booking_form.html` for the user interface.

4. **Static Files**:
   - CSS file(s) located in the `static` directory.

5. **README.md**:
   - This file, providing project overview and setup instructions.

## Technology Stack

- Backend: Python with FastAPI framework
- Database: SQLite3
- Frontend: HTML with Jinja2 templating, CSS
- Additional: SQLAlchemy for ORM

## Setup and Installation

1. Clone the repository
2. Run the application: `uvicorn main:app --reload`
