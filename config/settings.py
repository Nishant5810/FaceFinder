# FaceFinder Configuration Settings

# Face Detection Configuration
SIMILARITY_THRESHOLD = 65  # Percentage (0-100)
CONFIDENCE_THRESHOLD = 50  # Percentage (0-100)
QUALITY_THRESHOLD = 70     # Percentage (0-100)

# Feature Extraction
FEATURE_DIMENSIONS = 755  # Total number of features extracted per face
FACE_DETECTION_METHOD = "dual-cascade"

# Similarity Metrics
SIMILARITY_METRICS = ["cosine", "euclidean", "correlation"]
COSINE_WEIGHT = 0.40
EUCLIDEAN_WEIGHT = 0.30
CORRELATION_WEIGHT = 0.30

# Flask Configuration
UPLOAD_FOLDER = "uploads"
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp"}

# Cache Configuration
CACHE_FILE = "embeddings_trustworthy.pkl"
CACHE_DIRECTORY = "./"
