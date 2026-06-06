# Project Structure Guide

## Directory Organization

```
FaceFinder/
├── src/                          # Main application code
│   ├── __init__.py
│   ├── app.py                   # Flask application entry point
│   └── db_config.py             # Database configuration and operations
│
├── config/                       # Configuration files
│   ├── __init__.py
│   └── settings.py              # Application settings
│
├── static/                       # Static web assets
│   ├── css/
│   ├── js/
│   └── members/                 # Member profile photos
│
├── templates/                    # HTML templates
│   └── index.html               # Main web interface
│
├── docs/                         # Documentation
│   └── ARCHITECTURE.md          # System architecture
│
├── tests/                        # Test files
│   └── test_face_matching.py
│
├── uploads/                      # Temporary file uploads
│
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
├── .gitattributes               # Git attributes for line endings
├── .env.example                 # Environment variables template
├── README.md                     # Project overview
├── CONTRIBUTING.md              # Contribution guidelines
└── LICENSE                       # Project license
```

## Important Notes

- **src/**: Contains all source code
- **static/**: Web assets and member photos
- **templates/**: HTML files for the web interface
- **uploads/**: Temporary directory (git-ignored)
- **config/**: Configuration files for different settings
- **docs/**: Additional documentation
- **tests/**: Test scripts and test cases

## Environment Variables

Create a `.env` file in the root directory:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=face_recognition
DB_PORT=3306
SQLITE_FALLBACK=True
FLASK_ENV=development
```

See `.env.example` for a template.
