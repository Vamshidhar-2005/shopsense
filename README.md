# ShopSense FastAPI E-Commerce Portal

A modern, responsive FastAPI web application for **ShopSense** featuring role-based Login (Vendor / Admin), Vendor Registration, and MySQL database integration.

## Project Structure

```
shopsense/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point & page routes
│   ├── database.py              # MySQL database connection (SQLAlchemy + PyMySQL)
│   ├── models.py                # SQLAlchemy models (Vendor, Admin tables)
│   ├── schemas.py               # Pydantic schemas for request validation
│   ├── auth.py                  # Password hashing (bcrypt) & session/auth utilities
│   ├── crud.py                  # Database CRUD operations
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Modern design system (clean cards, glassmorphism, responsive)
│   │   ├── js/
│   │   │   ├── login.js         # Role toggle, password eye icon, submit logic
│   │   │   └── register.js      # Form validation, password eye icon, async submission & redirect
│   │   └── images/
│   └── templates/
│       ├── base.html            # Layout wrapper
│       ├── login.html           # Login page template
│       ├── register.html        # Vendor Registration page template
│       └── admin_dashboard.html # Admin dashboard baseline
├── .env                         # Environment configuration file
├── .env.example                 # Environment configuration template
├── schema.sql                   # Raw MySQL schema creation script
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

## Database Schema (`vendors` Table)

```sql
CREATE TABLE IF NOT EXISTS vendors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) NULL,
    business_address TEXT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Setup & Running

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**:
   Edit `.env` if using a custom MySQL instance:
   ```ini
   MYSQL_DATABASE_URL=mysql+pymysql://root:password@localhost:3306/shopsense_db
   ```

3. **Start the Development Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Access Pages**:
   - Login Page: `http://localhost:8000/login`
   - Vendor Registration: `http://localhost:8000/register`
   - Admin Dashboard: `http://localhost:8000/admin/dashboard`
