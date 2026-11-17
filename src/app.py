"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import CredentialFileError, verify_teacher_credentials


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

TEACHER_CREDENTIALS_FILE = current_dir / "teachers.json"
SESSION_DURATION = timedelta(hours=8)
active_sessions: dict[str, tuple[str, datetime]] = {}


class TeacherLogin(BaseModel):
    username: str
    password: str


def require_teacher(
    teacher_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    token = teacher_session or ""
    session = active_sessions.get(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Teacher login required")

    username, expires_at = session
    if datetime.now(timezone.utc) >= expires_at:
        active_sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Teacher session expired")

    return {"username": username, "token": token}


@app.post("/auth/login")
def login(teacher: TeacherLogin, request: Request, response: Response):
    try:
        valid_credentials = verify_teacher_credentials(
            teacher.username, teacher.password, TEACHER_CREDENTIALS_FILE
        )
    except CredentialFileError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    if not valid_credentials:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    active_sessions[token] = (
        teacher.username,
        datetime.now(timezone.utc) + SESSION_DURATION,
    )
    response.set_cookie(
        key="teacher_session",
        value=token,
        max_age=int(SESSION_DURATION.total_seconds()),
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
    )
    return {"username": teacher.username}


@app.get("/auth/me")
def get_teacher_session(
    teacher: dict[str, str] = Depends(require_teacher),
):
    return {"username": teacher["username"]}


@app.post("/auth/logout")
def logout(
    response: Response,
    teacher: dict[str, str] = Depends(require_teacher),
):
    active_sessions.pop(teacher["token"], None)
    response.delete_cookie(
        key="teacher_session",
        httponly=True,
        samesite="lax",
    )
    return {"message": "Logged out"}


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: dict[str, str] = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: dict[str, str] = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
