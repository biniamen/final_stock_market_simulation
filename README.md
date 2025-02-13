# Final Stock Market Simulation

A web application that simulates stock market operations. The project is divided into two main parts:

- **Backend:** A Django application that handles API endpoints, business logic, and data persistence.
- **Frontend:** An Angular application that provides a dynamic, responsive user interface.

This guide will help you set up the project on your local machine.

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
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

- **User Authentication:** Secure login and registration endpoints.
- **Stock Market Simulation:** Simulate trading operations such as buying and selling stocks.
- **Portfolio Management:** Track user investments and real-time updates of gains and losses.
- **RESTful API:** The backend exposes a set of APIs consumed by the Angular frontend.
- **Responsive UI:** The Angular frontend is built with modern web standards to work on desktops and mobile devices.

---

## Project Structure

```plaintext
final_stock_market_simulation/
├── backend/
│   ├── final_stock_market_simulation/    # Django project settings
│   ├── apps/                             # Django apps (e.g., accounts, trading, etc.)
│   ├── manage.py                         # Django management script
│   ├── requirements.txt                  # Python dependencies
│   └── README_backend.md                 # (Optional) Backend-specific documentation
│
├── frontend/
│   ├── src/
│   │   ├── app/                          # Angular components, services, and modules
│   │   ├── assets/                       # Images, styles, and other static assets
│   │   └── environments/                 # Environment configuration files
│   ├── angular.json                      # Angular CLI configuration
│   ├── package.json                      # Node dependencies for Angular
│   └── README_frontend.md                # (Optional) Frontend-specific documentation
│
├── .gitignore
└── README.md                             # This file
