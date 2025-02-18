# Final Stock Market Simulation

A full-stack web application for simulating stock market operations, built with **Django (Python)** for the backend and **Angular** for the frontend. This project provides user authentication, real-time stock data simulation, and portfolio management features.

---

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
   - [Backend (Django)](#backend-django)
   - [Frontend (Angular)](#frontend-angular)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)


---

## Features

- **User Authentication:** Secure registration and login with JWT-based authentication.
- **Stock Market Simulation:** Buy and sell stocks in a simulated environment.
- **Portfolio Management:** View and track investments with real-time gain/loss updates.
- **RESTful API:** Django REST Framework powers a comprehensive API consumed by the Angular frontend.
- **Responsive UI:** Modern, mobile-friendly Angular interface using Bootstrap and Angular Material.

---

## Project Structure

```plaintext
final_stock_market_simulation/
├── backend/
│   ├── final_stock_market_simulation/        # Django project settings (example: ethio_stock_simulation)
│   ├── apps/                                 # Django apps (e.g., users, stocks, regulations, etc.)
│   ├── manage.py                             # Django management script
│   ├── requirements.txt                      # Python dependencies
│   └── README_backend.md                     # (Optional) Backend-specific documentation
│
├── frontend/
│   ├── src/
│   │   ├── app/                              # Angular components, services, and modules
│   │   ├── assets/                           # Static assets (images, styles, etc.)
│   │   └── environments/                     # Environment configuration files
│   ├── angular.json                          # Angular CLI configuration
│   ├── package.json                          # Node dependencies for Angular
│   └── README_frontend.md                    # (Optional) Frontend-specific documentation
│
├── .gitignore
└── README.md                                 # This file


## Prerequisites
Python 3.9+

Download & Install Python
Node.js (v14+ recommended)

Download & Install Node.js
PostgreSQL

Download & Install PostgreSQL
Virtual Environment (Recommended)

Ensure you have a way to create and activate a Python virtual environment (e.g., venv).
Git (optional but recommended for version control)

Download & Install Git

## Installation
Backend (Django)
Clone the repository (or download the source code):


git clone https://github.com/your-username/final_stock_market_simulation.git
cd final_stock_market_simulation/backend
Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate   # On macOS/Linux
# or
venv\Scripts\activate      # On Windows
Install backend dependencies:

pip install -r requirements.txt
The requirements.txt might include (but is not limited to):


asgiref==3.8.1
Django==5.1.1
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
PyJWT==2.9.0
sqlparse==0.5.1
tzdata==2024.2
Configure the database (PostgreSQL):

Make sure PostgreSQL is running.

Update the database credentials in settings.py or a .env file if needed:


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ethio_stock_simulation_db',
        'USER': 'stock_user',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

Run Migrations:

python manage.py migrate
(Optional) Create a superuser:

python manage.py createsuperuser


Frontend (Angular)
Navigate to the frontend folder:


cd ../frontend
Install Node dependencies:

npm install
Your package.json includes (but is not limited to) the following dependencies:

{
  "name": "stock-simulation-frontend",
  "version": "0.0.0",
  "scripts": {
    "ng": "ng",
    "start": "ng serve",
    "build": "ng build",
    "watch": "ng build --watch --configuration development",
    "test": "ng test"
  },
  "private": true,
  "dependencies": {
    "@angular/animations": "^14.3.0",
    "@angular/cdk": "^13.0.0",
    "@angular/common": "^14.3.0",
    "@angular/compiler": "^14.2.0",
    "@angular/core": "^14.2.0",
    "@angular/forms": "^14.3.0",
    "@angular/material": "^13.0.0",
    "@angular/platform-browser": "^14.2.0",
    "@angular/platform-browser-dynamic": "^14.2.0",
    "@angular/router": "^14.2.0",
    "bootstrap": "^5.3.3",
    "bootstrap-icons": "^1.11.3",
    "decimal.js": "^10.5.0",
    "echarts": "^5.6.0",
    "file-saver": "^2.0.5",
    "jwt-decode": "^4.0.0",
    "ng-recaptcha": "^10.0.0",
    "ngx-echarts": "^19.0.0",
    "ngx-pagination": "^6.0.3",
    "ngx-toastr": "^14.0.0",
    "rxjs": "~7.5.0",
    "tslib": "^2.3.0",
    "xlsx": "^0.18.5",
    "zone.js": "~0.11.4"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^14.2.13",
    "@angular/cli": "~14.2.13",
    "@angular/compiler-cli": "^14.2.0",
    "@types/file-saver": "^2.0.7",
    "@types/jasmine": "~4.0.0",
    "@types/node": "^14.18.63",
    "@types/xlsx": "^0.0.36",
    "jasmine-core": "~4.3.0",
    "karma": "~6.4.0",
    "karma-chrome-launcher": "~3.1.0",
    "karma-coverage": "~2.2.0",
    "karma-jasmine": "~5.1.0",
    "karma-jasmine-html-reporter": "~2.0.0",
    "typescript": "~4.7.2"
  }
}
## Configuration
Environment Variables
Create a .env file in your backend project directory (at the same level as manage.py) and set the necessary environment variables. For example:


SENDGRID_API_KEY=YOUR_SENDGRID_API_KEY
SENDGRID_FROM_EMAIL=YOUR_VERIFIED_SENDER_EMAIL
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=YOUR_SENDGRID_API_KEY
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Ethiopian Stock Market <your_verified_email@example.com>
Adjust the values to match your own environment and secrets.

Important Settings Snippet
Below is a snippet of key settings from the Django settings.py for reference:

import os
from pathlib import Path
from decouple import config
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'django-insecure-o)%rqe3abw1de6...'
DEBUG = True
ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ethio_stock_simulation_db',
        'USER': 'stock_user',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'corsheaders',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'users',
    'stocks',
    'regulations',
    'debug_toolbar',
    'channels',
    # etc...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.CustomJWTAuthentication',
    ),
    # ...
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Logging, SendGrid, reCAPTCHA, etc.
Note: Always keep secret keys and sensitive credentials in your environment variables (not directly in settings.py).

## Running the Application
Backend Server (Django):

Ensure your virtual environment is activated:

cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows
Start the Django development server:

python manage.py runserver
By default, the backend will be available at http://127.0.0.1:8000/.
Frontend Server (Angular):

In a new terminal, navigate to the frontend folder:

cd frontend
Run the Angular development server:

npm start
By default, the frontend will be available at http://localhost:4200/.
