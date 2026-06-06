# FaceFinder Architecture

## System Overview

FaceFinder is a trustworthy face similarity matching application built with Flask. It uses multi-feature extraction and ensemble methods to provide accurate face recognition.

## Core Components

### 1. Application Layer (src/app.py)

- Flask web server
- REST API endpoints
- File upload handling
- Web interface serving

### 2. Face Recognition Engine

- **Face Detection**: Dual-cascade validation
- **Feature Extraction**: 755+ dimensional feature vectors
  - LBP histograms (512 features)
  - Edge/gradient features (96 features)
  - Corner detection (35 features)
  - Structural proportions (48 features)
  - Grid texture analysis (96 features)

### 3. Similarity Matching

- **Cosine Similarity** (40% weight)
- **Euclidean Similarity** (30% weight)
- **Correlation Similarity** (30% weight)
- **Confidence Scoring**: Based on metric agreement

### 4. Database Layer (src/db_config.py)

- MySQL primary database
- SQLite fallback
- Member data storage
- Query operations

## Data Flow

```
User Upload
    ↓
Face Detection & Validation
    ↓
Feature Extraction (755+ features)
    ↓
Similarity Computation (3-metric ensemble)
    ↓
Validation Checks
  - Quality >= 70%?
  - Similarity >= 65%?
  - Confidence >= 50%?
    ↓
Results Display
```

## Configuration

See `config/settings.py` for:

- Similarity thresholds
- Quality requirements
- Feature dimensions
- Metric weights

## Performance Metrics

- **Similarity Threshold**: 65%
- **Confidence Threshold**: 50%
- **Quality Threshold**: 70%
- **Feature Extraction**: 755+ dimensional vectors
