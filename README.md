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
7. [Contributing](#contributing)
8. [License](#license)

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
