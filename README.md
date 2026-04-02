# IronLog / Fitness Tracker

A Flask-based fitness tracking web app for logging workouts, tracking body measurements, and monitoring strength progress over time.

This project uses a simple SQLite database, server-rendered HTML templates, and a lightweight frontend for charts and workout management.

## Features

- User registration and login
- Dashboard with weekly stats, streaks, recent workouts, and personal records
- Create and view workouts with exercises, sets, reps, and weight
- Automatic personal record tracking based on logged sets
- Body measurement tracking including weight, body fat, muscle mass, and measurements
- Progress APIs for workout volume, exercise performance, and bodyweight trends
- Profile page for updating personal fitness details and goals
- Simple Windows startup script for quick local setup

## Tech Stack

- Python
- Flask
- SQLite
- HTML / Jinja templates
- CSS
- JavaScript
- Chart.js

## Project Structure

```text
Fitness_Tracker/
|-- app.py
|-- gymtracker.db
|-- requirements.txt
|-- start.bat
|-- Static/
|   |-- css/
|   `-- js/
`-- Templates/
    |-- auth.html
    |-- base.html
    |-- body_stats.html
    |-- dashboard.html
    |-- landing.html
    |-- new_workout.html
    |-- profile.html
    |-- progress.html
    |-- view_workout.html
    `-- workouts.html
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Fitness_Tracker.git
cd Fitness_Tracker
```

### 2. Create and activate a virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

The app will start locally at:

```text
http://127.0.0.1:5000
```

## Quick Start on Windows

If you are on Windows, you can also use:

```bat
start.bat
```

This script:

- checks that Python is installed
- creates a virtual environment
- installs Flask dependencies
- starts the app

## Database

The app uses a local SQLite database file:

```text
gymtracker.db
```

`app.py` automatically creates the required tables if they do not already exist.

The current project already includes a database file with sample data, so if you want a completely fresh start you can remove `gymtracker.db` and run the app again to recreate the schema.

## Main Functional Areas

### Authentication

- Register a new account
- Log in and log out with session-based authentication

### Workout Tracking

- Create workouts with a name, date, duration, and notes
- Add multiple exercises per workout
- Add multiple sets with reps and weight for each exercise
- View workout details and training volume

### Progress Tracking

- See recent personal records
- Track total and weekly workouts
- View volume-based progress data
- Track bodyweight and body stats over time

### Profile Management

- Update name, age, height, weight, and training goal

## API Endpoints

The app includes JSON endpoints used by the frontend:

- `/api/progress/volume`
- `/api/progress/exercise/<name>`
- `/api/progress/bodyweight`
- `/api/exercises/names`
- `/api/dashboard/weekly`

## Notes

- The UI branding in templates uses the name `IronLog`, while the repository folder is named `Fitness_Tracker`.
- The application is currently configured for local development and uses a hardcoded Flask secret key in `app.py`.
- SQLite makes this project easy to run locally without extra setup.

## Future Improvements

- Add edit functionality for workouts and exercises
- Add exercise categories and filters
- Add charts directly on more pages
- Add export/import support
- Add unit tests and better configuration management
- Move secrets and environment-specific settings into environment variables

## License

This project is open for personal use and learning. Add a license file if you plan to publish or distribute it publicly.
"# Fitness_Tracker" 
