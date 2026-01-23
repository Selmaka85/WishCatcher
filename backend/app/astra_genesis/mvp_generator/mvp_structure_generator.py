"""
MVP Structure Generator - Generează structură MVP pentru proiecte software
Cu boilerplate code complet, comentarii și explicații
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


class MVPStructureGenerator:
    """Generează structură MVP pentru wish-uri software cu boilerplate code complet"""
    
    def __init__(self):
        self.component_templates = {
            "auth": {
                "files": ["auth.py", "models.py", "utils.py"],
                "dependencies": ["fastapi", "python-jose[cryptography]", "passlib[bcrypt]"]
            },
            "database": {
                "files": ["database.py", "models.py", "schemas.py"],
                "dependencies": ["sqlalchemy==2.0.23", "mysql-connector-python"]
            },
            "api": {
                "files": ["routes.py", "schemas.py", "dependencies.py"],
                "dependencies": ["fastapi", "pydantic", "httpx"]
            },
            "frontend": {
                "files": ["index.tsx", "components/", "lib/"],
                "dependencies": ["next", "react", "tailwindcss"]
            }
        }
    
    def generate(
        self,
        wish_id: str,
        business_plan_id: Optional[str] = None,
        wish_data: Optional[Dict] = None
    ) -> Dict:
        """
        Generează structură MVP
        
        Args:
            wish_id: ID-ul wish-ului
            business_plan_id: ID-ul business plan-ului (opțional)
            wish_data: Datele wish-ului (opțional, dacă nu e furnizat, va încerca să le încarce)
        
        Returns:
            {
                "structure": {...},
                "files": [...]
            }
        """
        # Extract components from wish (folosește structured dacă există)
        components = self._extract_components(wish_id, wish_data)
        
        # Generate structure
        structure = self._generate_structure(components, wish_data)
        
        # Generate files
        files = self._generate_files(components, structure, wish_data)
        
        return {
            "structure": structure,
            "files": files
        }
    
    def _extract_components(self, wish_id: str, wish_data: Optional[Dict] = None) -> List[str]:
        """Extrage componente necesare din wish (folosește structured)"""
        components = ["api", "frontend"]  # Default
        
        if wish_data:
            structured = wish_data.get("structured", {})
            if structured:
                # Extrage din structured.how și key_features
                how = structured.get("how", "").lower()
                key_features = structured.get("key_features", [])
                
                # Detectează componente necesare
                if any(kw in how for kw in ["auth", "login", "user", "account", "sign"]):
                    components.append("auth")
                
                if any(kw in how for kw in ["database", "db", "store", "save", "data"]):
                    components.append("database")
                
                # Verifică și în key_features
                for feature in key_features:
                    feature_lower = feature.lower()
                    if "auth" in feature_lower or "login" in feature_lower:
                        if "auth" not in components:
                            components.append("auth")
                    if "database" in feature_lower or "storage" in feature_lower:
                        if "database" not in components:
                            components.append("database")
        
        return components
    
    def _generate_structure(self, components: List[str], wish_data: Optional[Dict] = None) -> Dict:
        """Generează structură de foldere (folosește structured.what pentru nume)"""
        # Extrage nume proiect din structured.what
        project_name = "mvp_project"
        if wish_data:
            structured = wish_data.get("structured", {})
            if structured:
                what = structured.get("what", "")
                if what:
                    # Creează nume valid din "what"
                    project_name = what.lower().replace(" ", "_").replace("-", "_")
                    # Elimină caractere invalide
                    project_name = "".join(c for c in project_name if c.isalnum() or c in ["_", "-"])
                    project_name = project_name[:30]  # Limitează lungimea
        
        structure = {
            "project_name": project_name,
            "folders": {
                "backend": {
                    "app": {
                        "api": {},
                        "models": {},
                        "utils": {}
                    },
                    "requirements.txt": None
                },
                "frontend": {
                    "pages": {},
                    "components": {},
                    "lib": {}
                },
                "docs": {
                    "README.md": None,
                    "SETUP.md": None
                }
            }
        }
        
        # Add component-specific folders
        if "auth" in components:
            structure["folders"]["backend"]["app"]["auth"] = {}
        
        if "database" in components:
            structure["folders"]["backend"]["app"]["database"] = {}
        
        return structure
    
    def _generate_files(self, components: List[str], structure: Dict, wish_data: Optional[Dict] = None) -> List[Dict]:
        """Generează lista de fișiere (folosește structured pentru conținut)"""
        files = []
        
        # Backend files
        files.append({
            "path": "backend/requirements.txt",
            "content": self._generate_requirements_txt(components),
            "type": "text"
        })
        
        files.append({
            "path": "backend/app/main.py",
            "content": self._generate_main_py(components, wish_data),
            "type": "python"
        })
        
        # Component files
        for component in components:
            if component in self.component_templates:
                template = self.component_templates[component]
                for file_name in template["files"]:
                    files.append({
                        "path": f"backend/app/{component}/{file_name}",
                        "content": self._generate_component_file(component, file_name),
                        "type": "python" if file_name.endswith(".py") else "typescript"
                    })
        
        # Frontend files
        if "frontend" in components:
            files.append({
                "path": "frontend/package.json",
                "content": self._generate_package_json(),
                "type": "json"
            })
        
        # Documentation
        files.append({
            "path": "README.md",
            "content": self._generate_readme(components, wish_data),
            "type": "markdown"
        })
        
        return files
    
    def _generate_requirements_txt(self, components: List[str]) -> str:
        """Generează requirements.txt cu toate dependențele"""
        base_deps = [
            "# FastAPI & Server",
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "",
            "# Utilities",
            "python-dotenv==1.0.0",
            "python-multipart==0.0.6"
        ]
        
        component_deps = {
            "auth": [
                "",
                "# Authentication",
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4"
            ],
            "database": [
                "",
                "# Database",
                "sqlalchemy==2.0.23",
                "mysql-connector-python==8.2.0"
            ],
            "api": [
                "",
                "# HTTP Client",
                "httpx==0.25.2"
            ]
        }
        
        deps = base_deps.copy()
        for component in components:
            if component in component_deps:
                deps.extend(component_deps[component])
        
        return "\n".join(deps)
    
    def _generate_main_py(self, components: List[str], wish_data: Optional[Dict] = None) -> str:
        """Generează main.py (folosește structured pentru descriere)"""
        imports = ["from fastapi import FastAPI"]
        
        if "auth" in components:
            imports.append("from app.auth import router as auth_router")
        
        if "api" in components:
            imports.append("from app.api import router as api_router")
        
        code = "\n".join(imports)
        
        # Adaugă descriere din structured dacă există
        description = ""
        if wish_data:
            structured = wish_data.get("structured", {})
            if structured:
                what = structured.get("what", "")
                if what:
                    description = f'    description="{what}"'
        
        code += f"\n\napp = FastAPI({description})\n\n"
        
        if "auth" in components:
            code += "app.include_router(auth_router)\n"
        
        if "api" in components:
            code += "app.include_router(api_router)\n"
        
        code += "\n@app.get('/')\nasync def root():\n    return {'status': 'ok'}\n"
        
        return code
    
    def _generate_component_file(self, component: str, file_name: str) -> str:
        """
        Generează fișier pentru componentă cu boilerplate code complet
        """
        if component == "auth" and file_name == "auth.py":
            return '''"""
Authentication Module
Generated by Astra Genesis MVP Generator

This module handles user authentication including:
- User registration
- User login
- JWT token generation and validation
- Password hashing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# TODO: Move to environment variables
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Router for authentication endpoints
router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
    
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in token (usually user info)
        expires_delta: Optional expiration time delta
    
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register")
async def register(username: str, password: str, email: str):
    """
    Register a new user.
    
    Args:
        username: Username for the new user
        password: Password for the new user
        email: Email address for the new user
    
    Returns:
        dict: Success message and user info
    
    TODO:
        - Validate email format
        - Check if username/email already exists
        - Save user to database
        - Send verification email
    """
    # TODO: Implement user registration logic
    # 1. Check if user exists
    # 2. Hash password
    # 3. Save to database
    # 4. Return success
    
    return {
        "message": "User registered successfully",
        "username": username,
        "email": email
    }


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint - returns JWT token.
    
    Args:
        form_data: OAuth2 form data (username, password)
    
    Returns:
        dict: Access token and token type
    
    TODO:
        - Verify user credentials from database
        - Return JWT token on success
    """
    # TODO: Implement login logic
    # 1. Get user from database by username
    # 2. Verify password
    # 3. Generate JWT token
    # 4. Return token
    
    return {
        "access_token": "example-token",
        "token_type": "bearer"
    }


@router.get("/me")
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current authenticated user.
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        dict: Current user information
    
    TODO:
        - Decode and validate JWT token
        - Get user from database
        - Return user info
    """
    # TODO: Implement get current user logic
    # 1. Decode JWT token
    # 2. Get user from database
    # 3. Return user info
    
    return {
        "username": "example_user",
        "email": "user@example.com"
    }
'''
        
        elif component == "auth" and file_name == "models.py":
            return '''"""
Authentication Models
Generated by Astra Genesis MVP Generator

Database models for user authentication.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """
    User model for authentication.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        hashed_password: Hashed password (never store plain passwords!)
        is_active: Whether user account is active
        created_at: Account creation timestamp
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
'''
        
        elif component == "database" and file_name == "database.py":
            return '''"""
Database Configuration
Generated by Astra Genesis MVP Generator

This module handles database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# TODO: Update database URL from environment variables
# Example: DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mvp.db")
DATABASE_URL = "sqlite:///./mvp.db"  # SQLite for development
# For production, use: "mysql+pymysql://user:password@localhost/dbname"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Database dependency for FastAPI routes.
    
    Yields:
        Session: Database session
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''
        
        elif component == "api" and file_name == "routes.py":
            return '''"""
API Routes
Generated by Astra Genesis MVP Generator

Main API endpoints for the application.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db

router = APIRouter()


@router.get("/items")
async def get_items(db: Session = Depends(get_db)):
    """
    Get all items.
    
    Args:
        db: Database session
    
    Returns:
        list: List of items
    
    TODO:
        - Implement database query
        - Add pagination
        - Add filtering
    """
    # TODO: Implement get items logic
    # return db.query(Item).all()
    return {"items": []}


@router.post("/items")
async def create_item(db: Session = Depends(get_db)):
    """
    Create a new item.
    
    Args:
        db: Database session
    
    Returns:
        dict: Created item
    
    TODO:
        - Validate input data
        - Save to database
        - Return created item
    """
    # TODO: Implement create item logic
    return {"message": "Item created", "item": {}}


@router.get("/items/{item_id}")
async def get_item(item_id: int, db: Session = Depends(get_db)):
    """
    Get a specific item by ID.
    
    Args:
        item_id: Item ID
        db: Database session
    
    Returns:
        dict: Item data
    
    TODO:
        - Query database for item
        - Handle not found case
    """
    # TODO: Implement get item logic
    # item = db.query(Item).filter(Item.id == item_id).first()
    # if not item:
    #     raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "data": {}}
'''
        
        else:
            # Generic component file
            return f'''"""
{component.title()} - {file_name}
Generated by Astra Genesis MVP Generator

This file contains {component} related functionality.

TODO:
    - Implement {component} logic
    - Add error handling
    - Add logging
    - Add tests
"""

# TODO: Add imports as needed
# from fastapi import ...
# from app.database import ...

# TODO: Implement {component} functionality
'''
    
    def _generate_package_json(self) -> str:
        """Generează package.json complet"""
        return json.dumps({
            "name": "mvp-frontend",
            "version": "1.0.0",
            "description": "Frontend application generated by Astra Genesis",
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "tailwindcss": "^3.0.0",
                "axios": "^1.6.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "typescript": "^5.0.0",
                "autoprefixer": "^10.0.0",
                "postcss": "^8.0.0"
            }
        }, indent=2)
    
    def _generate_readme(self, components: List[str], wish_data: Optional[Dict] = None) -> str:
        """Generează README complet cu instrucțiuni (folosește structured)"""
        # Extrage informații din structured
        project_name = "MVP Project"
        description = "This is a Minimum Viable Product (MVP) generated automatically from a validated business idea."
        what = ""
        problem = ""
        solution = ""
        
        if wish_data:
            structured = wish_data.get("structured", {})
            if structured:
                what = structured.get("what", "")
                problem = structured.get("problem", "")
                solution = structured.get("how", "")
                
                if what:
                    project_name = what.title()
                    description = f"This MVP addresses: {what}. Generated by Astra Genesis MVP Generator."
        
        problem_section = f"\n## Problem Solved\n\n{problem}\n" if problem and problem != "Problema identificată din context" else ""
        solution_section = f"\n## Solution Approach\n\n{solution}\n" if solution and solution != "Soluție bazată pe nevoile identificate" else ""
        
        return f'''# {project_name}

Generated by Astra Genesis MVP Generator

## Overview

{description}
The project structure includes boilerplate code with comments and explanations to help you get started quickly.
{problem_section}{solution_section}## Components

{chr(10).join(f"- **{c}**: {self._get_component_description(c)}" for c in components)}

## Project Structure

\`\`\`
mvp_project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/                 # API routes
│   │   ├── database/            # Database configuration and models
│   │   └── auth/                # Authentication module
│   └── requirements.txt         # Python dependencies
├── frontend/                     # Frontend application (if included)
└── README.md                    # This file
\`\`\`

## Setup Instructions

### Backend Setup

1. **Install dependencies:**
   \`\`\`bash
   cd backend
   pip install -r requirements.txt
   \`\`\`

2. **Configure database:**
   - Update `app/database/database.py` with your database URL
   - For SQLite (development): Already configured
   - For MySQL/PostgreSQL: Update DATABASE_URL

3. **Run the application:**
   \`\`\`bash
   uvicorn app.main:app --reload
   \`\`\`

4. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Frontend Setup (if included)

1. **Install dependencies:**
   \`\`\`bash
   cd frontend
   npm install
   \`\`\`

2. **Run development server:**
   \`\`\`bash
   npm run dev
   \`\`\`

3. **Access frontend:**
   - URL: http://localhost:3000

## Development Guidelines

### Code Structure

- **Boilerplate code** is provided with TODO comments
- **Functions** have docstrings explaining their purpose
- **Imports** are included but may need adjustment
- **Error handling** should be added where marked

### Next Steps

1. **Review generated code** and understand the structure
2. **Complete TODO items** in each file
3. **Add business logic** specific to your use case
4. **Configure environment variables** for production
5. **Add tests** for critical functionality
6. **Set up CI/CD** for deployment

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

Create a `.env` file in the backend directory:

\`\`\`
DATABASE_URL=sqlite:///./mvp.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
\`\`\`

## Support

For questions or issues:
- Review code comments in generated files
- Check FastAPI documentation: https://fastapi.tiangolo.com/
- Check Next.js documentation: https://nextjs.org/docs

---

**Generated by Astra Genesis MVP Generator**
**Version:** 1.0.0
**Generated at:** {datetime.now().isoformat()}
'''
    
    def _get_component_description(self, component: str) -> str:
        """Returnează descrierea componentei"""
        descriptions = {
            "auth": "User authentication and authorization",
            "database": "Database models and configuration",
            "api": "REST API endpoints",
            "frontend": "Frontend application (Next.js + React)"
        }
        return descriptions.get(component, "Component functionality")
