# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teachers can sign up and unregister students after logging in
- Students and visitors can browse activities and see who is registered

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account. The password is stored as a PBKDF2 hash in a local
   `teachers.json` file, which is excluded from Git:

   ```
   cd src
   python create_teacher.py
   ```

3. Start the application from the `src` directory:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                             | Description                                             |
| ------ | -------------------------------------------------------------------- | ------------------------------------------------------- |
| GET    | `/activities`                                                        | Get activities and current participant counts (public) |
| POST   | `/auth/login`                                                        | Log in as a teacher; sets an HTTP-only session cookie   |
| GET    | `/auth/me`                                                           | Get the current teacher session                        |
| POST   | `/auth/logout`                                                       | End the current teacher session                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`    | Sign up a student (teacher login required)              |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)           |

Teacher sessions expire after eight hours and are cleared when the server
restarts. Use HTTPS in deployments so the session cookie is marked secure.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and participant data is stored in memory, so it resets when the server
restarts. Teacher credentials are stored separately in `teachers.json`.
