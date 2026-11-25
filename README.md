# Healthcare Backend API System

A production-grade, secure healthcare backend system built with **Django**, **Django REST Framework (DRF)**, **PostgreSQL** in Docker, and **JWT Authentication** (`djangorestframework-simplejwt`).

This application allows medical practitioners and healthcare staff to register, authenticate, manage patient records with **strict ownership isolation**, maintain doctor directories, and assign doctors to patients with duplicate-prevention rules.

---

## 🌟 Key Features

- **Modern Authentication**: Custom User model using `email` as the primary credential + `name` + `password`.
- **JWT Security**: Access and refresh tokens with automatic token rotation and blacklist support.
- **Strict Ownership Data Isolation**: Authenticated users can create, view, update, and delete **only their own** patients. Cross-user data access is strictly forbidden (returns 404).
- **Doctor Directory**: Platform-wide directory for medical practitioners with validation on credentials and contact details.
- **Patient-Doctor Mapping**: Assign doctors to patients with database-level uniqueness constraints preventing duplicate mappings, plus quick lookup of all doctors assigned to any patient.
- **PostgreSQL in Docker**: Fully containerized PostgreSQL 16 database with persistence and healthcheck via `docker-compose.yml`.
- **OpenAPI 3 / Swagger Documentation**: Interactive API documentation generated dynamically via `drf-spectacular` at `/api/docs/`.
- **Standardized Error Handling**: Unified JSON error envelope across the entire API (`success: false`, `error: {...}`).
- **Production Logging**: Rotating file logging (`logs/healthcare.log`) and standard console outputs with timestamps and source lines.
- **Complete Test Suite**: 23 automated unit and integration tests passing at 100%.
- **Ready-to-use Postman Collection**: `healthcare_api.postman_collection.json` with pre-configured environment variables and automated token extractors.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | Django 5.1 & Django REST Framework (DRF) 3.17 |
| **Database** | PostgreSQL 16 (via Docker container) |
| **DB Driver** | `psycopg2-binary` 2.9 |
| **Authentication** | `djangorestframework-simplejwt` 5.5 |
| **API Docs** | `drf-spectacular` 0.30 (Swagger UI & ReDoc) |
| **Testing** | `pytest` 9.2 & `pytest-django` 4.14 |
| **Configuration** | `python-dotenv` 1.2 |

---

## 📁 Project Architecture

```text
Healthcare_Backend/
├── .env.example                          # Environment variables template
├── .env                                  # Local environment configuration
├── docker-compose.yml                    # PostgreSQL 16 container definition
├── requirements.txt                      # Project dependencies
├── pytest.ini                            # Pytest configuration
├── manage.py                             # Django CLI utility
├── schema.yml                            # OpenAPI 3 YAML schema
├── healthcare_api.postman_collection.json # Postman Collection v2.1
├── core/                                 # Project configuration root
│   ├── settings.py                       # PostgreSQL, JWT, Logging & DRF settings
│   ├── urls.py                           # Root API router & Swagger mounting
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── authentication/                   # Custom User model & JWT auth
│   │   ├── models.py                     # Custom User & CustomUserManager
│   │   ├── serializers.py                # Register & Login serializers
│   │   ├── views.py                      # RegisterView, LoginView
│   │   ├── test_auth.py                  # Unit tests for authentication
│   │   └── urls.py
│   ├── patients/                         # Patient management (Strict Ownership)
│   │   ├── models.py                     # Patient model (created_by FK)
│   │   ├── permissions.py                # IsOwner object permission
│   │   ├── serializers.py                # PatientSerializer
│   │   ├── views.py                      # Scoped List, Create, Retrieve, Update, Delete
│   │   ├── test_patients.py              # Unit tests for patient ownership
│   │   └── urls.py
│   ├── doctors/                          # Doctor directory
│   │   ├── models.py                     # Doctor model
│   │   ├── serializers.py                # DoctorSerializer
│   │   ├── views.py                      # Doctor CRUD views
│   │   ├── test_doctors.py               # Unit tests for doctors
│   │   └── urls.py
│   └── mappings/                         # Patient-Doctor associations
│       ├── models.py                     # PatientDoctorMapping (unique_together)
│       ├── serializers.py                # Mapping serializers (nested)
│       ├── views.py                      # Assign, List, Patient Lookup, Delete
│       ├── test_mappings.py              # Unit tests for mappings
│       └── urls.py
├── common/                               # Reusable modules
│   ├── exceptions.py                     # Unified JSON error response handler
│   └── pagination.py                     # Standard pagination class
└── logs/
    └── healthcare.log                    # Production rotating log file
```

---

## 🚀 Quick Start Guide

### 1. Clone & Set Up Environment

```bash
# Navigate into the project directory
cd Healthcare_Backend

# Create and activate virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Your `.env` file should look like:
```ini
DJANGO_SECRET_KEY=healthcare-super-secret-key-change-in-production-1234567890!@#$
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# PostgreSQL Configuration
DB_NAME=healthcare_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# SimpleJWT Configuration
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

### 3. Start PostgreSQL Database (Docker)

Start the PostgreSQL 16 container in the background:
```bash
docker-compose up -d
```

Verify that the database container is healthy:
```bash
docker-compose ps
```

### 4. Run Migrations & Create Superuser

```bash
# Apply all database migrations
python manage.py migrate

# (Optional) Create an administrative superuser
python manage.py createsuperuser
```

### 5. Start the Development Server

```bash
python manage.py runserver
```

The API will be live at `http://127.0.0.1:8000/`.

---

## 📖 API Documentation & Endpoints

### Interactive Documentation
- **Swagger UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **ReDoc**: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **OpenAPI 3 Schema**: [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

### Endpoint Reference Table

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| **POST** | `/api/auth/register/` | No | Register a new user (`name`, `email`, `password`) |
| **POST** | `/api/auth/login/` | No | Log in and receive JWT `access` & `refresh` tokens |
| **POST** | `/api/auth/token/refresh/` | No | Refresh an expired access token |
| **POST** | `/api/patients/` | **Yes** | Add a new patient record (auto-binds to creator) |
| **GET** | `/api/patients/` | **Yes** | Retrieve all patients created by the authenticated user |
| **GET** | `/api/patients/<id>/` | **Yes** | Get details of a specific patient (owner only) |
| **PUT/PATCH** | `/api/patients/<id>/` | **Yes** | Update patient details (owner only) |
| **DELETE** | `/api/patients/<id>/` | **Yes** | Delete a patient record (owner only) |
| **POST** | `/api/doctors/` | **Yes** | Register a new doctor record |
| **GET** | `/api/doctors/` | **Yes** | Retrieve all doctors across the platform |
| **GET** | `/api/doctors/<id>/` | **Yes** | Get details of a specific doctor |
| **PUT/PATCH** | `/api/doctors/<id>/` | **Yes** | Update doctor details |
| **DELETE** | `/api/doctors/<id>/` | **Yes** | Delete a doctor record |
| **POST** | `/api/mappings/` | **Yes** | Assign a doctor to a patient |
| **GET** | `/api/mappings/` | **Yes** | Retrieve all patient-doctor mappings |
| **GET** | `/api/mappings/<patient_id>/`| **Yes** | Get all doctors assigned to a specific patient |
| **DELETE** | `/api/mappings/<id>/` | **Yes** | Remove doctor assignment from patient |
| **GET** | `/api/health/` | No | Health check endpoint |

---

## 🔒 Security & Data Isolation Details

### 1. Strict Patient Ownership
Patient records belong strictly to the user who registered them:
- `PatientListCreateView.get_queryset()` strictly returns `Patient.objects.filter(created_by=request.user)`.
- Requesting `/api/patients/<id>/` for a patient created by another user automatically returns `404 Not Found`, preventing metadata probing or enumeration attacks.
- The `IsOwner` permission class provides secondary defense-in-depth on object mutations.

### 2. Standardized JSON Error Envelope
Every non-2xx response is intercepted by `common/exceptions.py` and returned in a unified format:
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Validation failed. Please correct the errors in the submitted data.",
    "details": {
      "email": [
        "A user with this email already exists."
      ]
    }
  }
}
```

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```bash
# Run all tests with verbose output
pytest
```

Or using Django's test runner:
```bash
python manage.py test apps.authentication apps.patients apps.doctors apps.mappings
```

### Test Coverage Highlights:
- **Authentication**: User registration, duplicate prevention, password length enforcement, valid login, invalid credentials, token refresh.
- **Patients**: Authenticated creation, unauthenticated rejection (401), strict list isolation across multiple users, detail access isolation, owner update and delete.
- **Doctors**: Creation, duplicate email prevention, full directory listing, detail retrieval, updates, and deletion.
- **Mappings**: Assigning doctor, duplicate assignment blocking, blocking assignment to another user's patient, retrieving assigned doctors for a specific patient, deleting mapping by owner, unauthorized delete prevention (403).

---

## 📮 Postman Collection Usage

1. Open Postman.
2. Click **Import** and select the file `healthcare_api.postman_collection.json`.
3. The collection is pre-configured with environment variables:
   - `{{base_url}}`: Defaults to `http://127.0.0.1:8000`
   - `{{access_token}}`: Automatically populated when you send the **Login User** request!
   - `{{patient_id}}`, `{{doctor_id}}`, `{{mapping_id}}`: Dynamically saved upon creation.
4. Execute the requests in numbered order:
   - `1. Authentication -> Login User & Get JWT Tokens`
   - `2. Patients -> Add New Patient`
   - `3. Doctors -> Add New Doctor`
   - `4. Patient-Doctor Mappings -> Assign Doctor to Patient`

---

## 📝 License
This project is open-source and created for technical assessment purposes.
