"""
CONSOLIDATED FACE SIMILARITY MATCHING APPLICATION
All-in-one intelligent face matching system with trustworthy validation
"""

import numpy as np
import os
from datetime import datetime
import json
from flask import Flask, render_template, request, jsonify, redirect
from werkzeug.utils import secure_filename
import cv2
from scipy.spatial.distance import cosine, euclidean
import hashlib
import warnings
import requests
import sys
import pickle
from pathlib import Path
from scipy import stats as scipy_stats

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.path.dirname(__file__))

# Try to import database manager, but don't fail if missing
try:
    from db_config import initialize_database, DB_CONFIG
    DB_MANAGER = initialize_database()
except:
    print("[WARN] Database configuration not available (optional)")
    DB_MANAGER = None

# ============================================================================
# TRUSTWORTHY FACE MATCHER - Consolidated Core Engine
# ============================================================================

class TrustworthyFaceMatcher:
    """
    Reliable face similarity using:
    1. Multiple robust feature types (not just raw pixels)
    2. Quality validation (face detection confidence)
    3. Statistical confidence scoring
    4. Conservative thresholds (prevent false positives)
    5. Ensemble matching methods
    """
    
    def __init__(self, cache_file="embeddings_trustworthy.pkl"):
        self.cache_file = cache_file
        self.embeddings = {}
        self.metadata = {}
        
        # Face detection cascades
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        lbp_path = cv2.data.haarcascades + 'lbpcascade_frontalface.xml'
        self.lbp_cascade = cv2.CascadeClassifier(lbp_path) if os.path.exists(lbp_path) else None
        
        print("[OK] Trustworthy matcher initialized")
        self.load_cache()
    
    def load_cache(self):
        """Load cached embeddings and metadata"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, dict) and 'embeddings' in data:
                        self.embeddings = data.get('embeddings', {})
                        self.metadata = data.get('metadata', {})
                    else:
                        self.embeddings = data if isinstance(data, dict) else {}
                        self.metadata = {}
            except Exception as e:
                print(f"[WARN] Could not load cache: {e}")
                self.embeddings = {}
                self.metadata = {}
    
    def save_cache(self):
        """Save embeddings and metadata to cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'metadata': self.metadata
                }, f)
        except Exception as e:
            print(f"[WARN] Could not save cache: {e}")
    
    def detect_face_with_quality(self, image):
        """
        Detect face with quality metrics
        Returns: (face_roi, quality_score, detection_method)
        """
        try:
            grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            faces_primary = self.face_cascade.detectMultiScale(
                grey, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
            )
            
            faces_lbp = []
            if self.lbp_cascade is not None:
                faces_lbp = self.lbp_cascade.detectMultiScale(
                    grey, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
                )
            
            if len(faces_primary) > 0:
                x, y, w, h = max(faces_primary, key=lambda f: f[2] * f[3])
                quality_score = 0.85
                
                if len(faces_lbp) > 0:
                    quality_score = 0.95
                
                padding = int(0.1 * w)
                x = max(0, x - padding)
                y = max(0, y - padding)
                h_padded = min(image.shape[0] - y, h + 2 * padding)
                w_padded = min(image.shape[1] - x, w + 2 * padding)
                
                face_roi = image[y:y+h_padded, x:x+w_padded].copy()
                
                if face_roi.size > 0:
                    return face_roi, quality_score, "primary"
            
            if len(faces_lbp) > 0:
                x, y, w, h = max(faces_lbp, key=lambda f: f[2] * f[3])
                quality_score = 0.75
                
                padding = int(0.1 * w)
                x = max(0, x - padding)
                y = max(0, y - padding)
                h_padded = min(image.shape[0] - y, h + 2 * padding)
                w_padded = min(image.shape[1] - x, w + 2 * padding)
                
                face_roi = image[y:y+h_padded, x:x+w_padded].copy()
                
                if face_roi.size > 0:
                    return face_roi, quality_score, "fallback"
            
            return None, 0.0, None
            
        except Exception as e:
            return None, 0.0, None
    
    def extract_robust_features(self, image_path):
        """Extract MULTIPLE robust features"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None, {"error": "Cannot read image"}
            
            face_roi, quality_score, detection_method = self.detect_face_with_quality(img)
            
            if face_roi is None:
                return None, {"error": "No face detected", "quality": 0.0}
            
            if quality_score < 0.7:
                return None, {"error": "Face detection quality too low", "quality": quality_score}
            
            grey = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            grey = cv2.resize(grey, (128, 128))
            
            features = []
            
            # Feature 1: LBP Histogram
            lbp_features = self._extract_lbp_histogram(grey)
            features.extend(lbp_features)
            
            # Feature 2: Edge Patterns
            edge_features = self._extract_edge_features(grey)
            features.extend(edge_features)
            
            # Feature 3: Corner Features
            corner_features = self._extract_corner_features(grey)
            features.extend(corner_features)
            
            # Feature 4: Structural Features
            structural_features = self._extract_structural_features(grey)
            features.extend(structural_features)
            
            # Feature 5: Grid Texture
            grid_features = self._extract_grid_texture(grey)
            features.extend(grid_features)
            
            features = np.array(features, dtype=np.float32)
            
            feature_mean = np.mean(features)
            feature_std = np.std(features)
            
            if feature_std > 0:
                features = (features - feature_mean) / feature_std
            
            metadata = {
                "detection_quality": float(quality_score),
                "detection_method": detection_method,
                "feature_dim": len(features),
                "feature_mean": float(feature_mean),
                "feature_std": float(feature_std),
                "face_size": max(face_roi.shape[:2])
            }
            
            return features, metadata
            
        except Exception as e:
            return None, {"error": str(e)}
    
    def _extract_lbp_histogram(self, grey):
        """Extract Local Binary Pattern histogram"""
        features = []
        
        for radius in [1, 2]:
            lbp = np.zeros_like(grey, dtype=np.uint8)
            h, w = grey.shape
            
            for i in range(radius, h - radius):
                for j in range(radius, w - radius):
                    center = grey[i, j]
                    
                    neighbors = np.array([
                        grey[i-radius, j-radius], grey[i-radius, j], grey[i-radius, j+radius],
                        grey[i, j+radius], grey[i+radius, j+radius], grey[i+radius, j],
                        grey[i+radius, j-radius], grey[i, j-radius]
                    ])
                    
                    lbp[i, j] = np.sum((neighbors > center) * (2 ** np.arange(8)))
            
            hist = np.bincount(lbp.flatten(), minlength=256)
            hist = hist / (np.sum(hist) + 1e-6)
            features.extend(hist[:256])
        
        return features
    
    def _extract_edge_features(self, grey):
        """Extract edge and gradient features"""
        features = []
        
        edges = cv2.Canny(grey, 30, 100)
        edge_hist = np.histogram(edges.flatten(), bins=32, range=(0, 256))[0]
        edge_hist = edge_hist / (np.sum(edge_hist) + 1e-6)
        features.extend(edge_hist)
        
        sobelx = cv2.Sobel(grey, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(grey, cv2.CV_32F, 0, 1, ksize=3)
        
        magnitude = np.sqrt(sobelx**2 + sobely**2)
        mag_hist = np.histogram(magnitude.flatten(), bins=32, range=(0, 200))[0]
        mag_hist = mag_hist / (np.sum(mag_hist) + 1e-6)
        features.extend(mag_hist)
        
        angle = np.arctan2(sobely, sobelx)
        angle_hist = np.histogram(angle.flatten(), bins=32, range=(-np.pi, np.pi))[0]
        angle_hist = angle_hist / (np.sum(angle_hist) + 1e-6)
        features.extend(angle_hist)
        
        return features
    
    def _extract_corner_features(self, grey):
        """Extract corner and keypoint features"""
        features = []
        
        corners = cv2.cornerHarris(grey, 2, 3, 0.04)
        
        corner_hist = np.histogram(corners.flatten(), bins=32)[0]
        corner_hist = corner_hist / (np.sum(corner_hist) + 1e-6)
        features.extend(corner_hist)
        
        features.append(np.mean(corners))
        features.append(np.std(corners))
        features.append(np.max(corners))
        
        return features
    
    def _extract_structural_features(self, grey):
        """Extract structural facial proportions"""
        features = []
        h, w = grey.shape
        
        hist = cv2.calcHist([grey], [0], None, [32], [0, 256])
        hist = hist.flatten() / (np.sum(hist) + 1e-6)
        features.extend(hist)
        
        for i in range(4):
            for j in range(4):
                y1, y2 = i * h // 4, (i + 1) * h // 4
                x1, x2 = j * w // 4, (j + 1) * w // 4
                
                region = grey[y1:y2, x1:x2]
                features.append(np.std(region))
                features.append(np.mean(region))
        
        return features
    
    def _extract_grid_texture(self, grey):
        """Extract grid-based texture patterns"""
        features = []
        grid_size = 4
        h, w = grey.shape
        
        for i in range(grid_size):
            for j in range(grid_size):
                y1, y2 = i * h // grid_size, (i + 1) * h // grid_size
                x1, x2 = j * w // grid_size, (j + 1) * w // grid_size
                
                cell = grey[y1:y2, x1:x2]
                
                features.append(np.std(cell))
                features.append(np.mean(cell))
                
                edges = cv2.Canny(cell, 20, 50)
                edge_density = np.sum(edges > 0) / (cell.size + 1e-6)
                features.append(edge_density)
        
        return features
    
    def compute_similarity_fast(self, features1, features2):
        """FAST similarity computation using only cosine distance"""
        if features1 is None or features2 is None:
            return 0.0, 0.0
        
        try:
            f1 = np.array(features1, dtype=np.float32).flatten()
            f2 = np.array(features2, dtype=np.float32).flatten()
            
            min_len = min(len(f1), len(f2))
            f1 = f1[:min_len]
            f2 = f2[:min_len]
            
            if min_len < 100:
                return 0.0, 0.0
            
            # Fast cosine similarity only
            cosine_sim = 1 - cosine(f1, f2)
            cosine_sim = max(0, min(1, cosine_sim))  # Clamp to [0, 1]
            
            # Simple confidence based on feature magnitude agreement
            mag1 = np.linalg.norm(f1)
            mag2 = np.linalg.norm(f2)
            magnitude_ratio = 1 - abs(mag1 - mag2) / (max(mag1, mag2) + 1e-6)
            confidence = (cosine_sim + magnitude_ratio) / 2.0
            
            return cosine_sim * 100, confidence * 100
        except:
            return 0.0, 0.0
    
    def compute_similarity_trustworthy(self, features1, features2):
        """Compute similarity using MULTIPLE metrics"""
        if features1 is None or features2 is None:
            return 0.0, 0.0, {"error": "Missing features"}
        
        try:
            f1 = np.array(features1, dtype=np.float32).flatten()
            f2 = np.array(features2, dtype=np.float32).flatten()
            
            min_len = min(len(f1), len(f2))
            f1 = f1[:min_len]
            f2 = f2[:min_len]
            
            if min_len < 100:
                return 0.0, 0.0, {"error": "Insufficient features"}
            
            # Cosine Similarity
            cosine_sim = 1 - cosine(f1, f2)
            
            # Euclidean Distance (normalized)
            euclidean_dist = euclidean(f1, f2)
            euclidean_sim = 1.0 / (1.0 + euclidean_dist)
            
            # Correlation-based
            correlation_sim = np.corrcoef(f1, f2)[0, 1]
            if np.isnan(correlation_sim):
                correlation_sim = 0.0
            correlation_sim = (correlation_sim + 1.0) / 2.0
            
            # Ensemble
            ensemble_similarity = (
                0.40 * cosine_sim +
                0.30 * euclidean_sim +
                0.30 * correlation_sim
            )
            
            metric_variance = np.var([cosine_sim, euclidean_sim, correlation_sim])
            confidence = 1.0 - min(metric_variance, 0.5)
            
            validation = {
                "cosine_similarity": float(cosine_sim),
                "euclidean_similarity": float(euclidean_sim),
                "correlation_similarity": float(correlation_sim),
                "ensemble_similarity": float(ensemble_similarity),
                "metric_agreement": float(confidence),
                "feature_count": int(min_len)
            }
            
            similarity_percent = ensemble_similarity * 100
            confidence_percent = confidence * 100
            
            return similarity_percent, confidence_percent, validation
            
        except Exception as e:
            return 0.0, 0.0, {"error": str(e)}
    
    def add_profile(self, name, image_path):
        """Add a member profile to the database"""
        try:
            features, metadata = self.extract_robust_features(image_path)
            
            if features is None:
                print(f"    [-] {name}: {metadata.get('error', 'Failed to extract features')}")
                return False
            
            self.embeddings[name] = features
            self.metadata[name] = metadata
            print(f"    [+] {name}")
            return True
            
        except Exception as e:
            print(f"    [-] {name}: {str(e)}")
            return False
    
    def find_similar_faces(self, image_path, threshold=60, top_k=5):
        """Find similar faces with optimized trustworthy validation"""
        try:
            test_features, test_metadata = self.extract_robust_features(image_path)
            
            if test_features is None:
                return {
                    "status": "error",
                    "message": test_metadata.get('error', 'Could not process image'),
                    "matches": [],
                    "detection_quality": test_metadata.get('quality', 0.0)
                }
            
            detection_quality = test_metadata.get('detection_quality', 0.0)
            if detection_quality < 0.7:
                return {
                    "status": "warning",
                    "message": f"Uploaded face detection quality is low ({detection_quality:.1%}). Results may be unreliable.",
                    "matches": [],
                    "detection_quality": detection_quality
                }
            
            similarities = {}
            
            # FAST PASS: Use fast similarity for all profiles
            for name, profile_features in self.embeddings.items():
                similarity, confidence = self.compute_similarity_fast(
                    test_features, profile_features
                )
                
                # Use lower threshold for initial filtering
                if similarity >= (threshold - 10) and confidence >= 40:
                    similarities[name] = {
                        "similarity": similarity,
                        "confidence": confidence
                    }
            
            if not similarities:
                return {
                    "status": "no_match",
                    "message": f"No confident matches found above {threshold}% threshold",
                    "matches": [],
                    "detection_quality": detection_quality
                }
            
            # Sort and get top candidates after fast pass
            sorted_candidates = sorted(
                similarities.items(),
                key=lambda x: (x[1]["similarity"], x[1]["confidence"]),
                reverse=True
            )[:top_k * 2]  # Get extra candidates for final filtering
            
            # THOROUGH PASS: Use trustworthy metrics only for top candidates
            final_matches = {}
            for name, fast_scores in sorted_candidates:
                similarity, confidence, _ = self.compute_similarity_trustworthy(
                    test_features, self.embeddings[name]
                )
                
                if similarity >= threshold and confidence >= 50:
                    final_matches[name] = {
                        "similarity": similarity,
                        "confidence": confidence
                    }
            
            if not final_matches:
                return {
                    "status": "no_match",
                    "message": f"No confident matches found above {threshold}% threshold",
                    "matches": [],
                    "detection_quality": detection_quality
                }
            
            sorted_matches = sorted(
                final_matches.items(),
                key=lambda x: (x[1]["similarity"], x[1]["confidence"]),
                reverse=True
            )[:top_k]
            
            formatted_matches = []
            for name, scores in sorted_matches:
                formatted_matches.append({
                    "name": name,
                    "similarity": round(scores["similarity"], 1),
                    "confidence": round(scores["confidence"], 1)
                })
            
            return {
                "status": "success",
                "message": f"Found {len(formatted_matches)} confident match(es)",
                "matches": formatted_matches,
                "detection_quality": detection_quality
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "matches": []
            }
    
    def get_stats(self):
        """Get database statistics"""
        return {
            'total_profiles': len(self.embeddings),
            'profiles': list(self.embeddings.keys())
        }

# ============================================================================
# CONFIGURATION & INITIALIZATION
# ============================================================================

MIN_SIMILARITY_THRESHOLD = 65
ENCODING_CACHE = {}
MEMBER_INDEX = {}
MEMBER_PROFILE_CACHE = {}  # NEW: Cache for member profiles with URLs

print('[*] Loading trustworthy face matcher...')
MATCHER = TrustworthyFaceMatcher()
print('[OK] Matcher initialized with multi-feature validation')

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def download_member_photo(photo_url, member_name):
    """Download and save external photo locally"""
    try:
        if photo_url.startswith('/static/') or photo_url.startswith('static/'):
            return photo_url
        
        response = requests.get(photo_url, timeout=5)
        response.raise_for_status()
        
        os.makedirs('static/members', exist_ok=True)
        filename = f"static/members/{member_name.replace(' ', '_').lower()}.jpg"
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return f"/{filename}"
    
    except Exception as e:
        print(f"[WARN] Could not download photo for {member_name}: {e}")
        return photo_url

def detect_gender_from_face_shape(image_path):
    """Fast gender detection using facial structure analysis"""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "Male"
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) == 0:
            return "Male"
        
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        gray_face = gray[y:y+h, x:x+w]
        
        h, w = gray_face.shape
        
        aspect_ratio = w / h if h > 0 else 0.75
        lower_third = gray_face[int(h*0.66):, :] if h > 0 else gray_face
        lower_std = np.std(lower_third) if lower_third.size > 0 else 0
        
        upper_third = gray_face[:int(h*0.33), :] if h > 0 else gray_face
        upper_std = np.std(upper_third) if upper_third.size > 0 else 0
        
        jaw_factor = lower_std - upper_std
        aspect_factor = (aspect_ratio - 0.77) * 50
        score = jaw_factor + aspect_factor
        
        return "Male" if score > 2 else "Female"
    
    except:
        return "Male"

def initialize_matcher_database():
    """Load member profiles from database and build face matcher"""
    try:
        if not DB_MANAGER:
            print("[ERROR] Database manager not initialized!")
            return False
        
        print("\n[*] Initializing face matcher database from MySQL...")
        
        members = DB_MANAGER.get_all_members()
        
        if not members:
            print("[WARN] No members found in MySQL database!")
            return False
        
        total_members = len(members)
        os.makedirs('static/members', exist_ok=True)
        
        print(f"[*] Processing {total_members} member(s)...\n")
        for idx, member in enumerate(members, 1):
            name = member["name"]
            photo_url = member["photo"]
            
            print(f"[{idx}/{total_members}] Processing {name}...", end=" ")
            
            if photo_url and photo_url.startswith('http'):
                try:
                    response = requests.get(photo_url, timeout=10)
                    response.raise_for_status()
                    
                    safe_name = name.replace(' ', '_').replace('/', '_').lower()
                    local_photo_path = f"static/members/{safe_name}.jpg"
                    
                    with open(local_photo_path, 'wb') as f:
                        f.write(response.content)
                    print(f"[OK Downloaded]")
                except Exception as e:
                    print(f"[WARN Download failed: {e}]")
                    continue
            else:
                safe_name = name.replace(' ', '_').replace('/', '_').lower()
                local_photo_path = f"static/members/{safe_name}.jpg"
                if photo_url and photo_url.startswith('/'):
                    photo_url = photo_url[1:]
                if photo_url and os.path.exists(photo_url) and not os.path.exists(local_photo_path):
                    import shutil
                    shutil.copy(photo_url, local_photo_path)
                print(f"[OK Local]")
        
        print("\n[*] Building face recognition database...")
        
        successful = 0
        for member in members:
            name = member["name"]
            safe_name = name.replace(' ', '_').replace('/', '_').lower()
            local_photo_path = f"static/members/{safe_name}.jpg"
            
            if os.path.exists(local_photo_path):
                try:
                    if MATCHER.add_profile(name, local_photo_path):
                        successful += 1
                except Exception as e:
                    print(f"[WARN] {name}: {e}")
        
        MATCHER.save_cache()
        
        if successful > 0:
            stats = MATCHER.get_stats()
            print(f"\n[OK] Database initialized successfully")
            print(f"[OK] Total profiles loaded: {successful}/{total_members}\n")
            return True
        else:
            print("[!] WARNING: No profiles could be loaded!")
            return False
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        return False

def load_members_info():
    """Load member information from database with fallback"""
    global MEMBER_PROFILE_CACHE
    try:
        if DB_MANAGER:
            try:
                members = DB_MANAGER.get_all_members()
            except:
                # If query fails, try reconnecting
                try:
                    DB_MANAGER.connect()
                    members = DB_MANAGER.get_all_members()
                except:
                    members = []
            
            info = {}
            for member in members:
                name = member.get('name', '')
                if name:
                    info[name] = member
                    # Cache profile link with member name as key
                    MEMBER_PROFILE_CACHE[name.lower()] = {
                        'id': member.get('id'),
                        'profile_link': member.get('profile_link', f"/member/{member.get('id', 1)}"),
                        'photo_url': member.get('photo', '')
                    }
            
            if info:
                print(f"[OK] Loaded {len(info)} members into cache with profile links")
            return info
    except Exception as e:
        print(f"[WARN] Could not load members from database: {e}")
    return {}

def build_match_object(name, similarity, confidence, member_info):
    """Helper function to build a match object with all required details"""
    # Try to get member info from cache first
    if not member_info:
        member_info = MEMBERS_INFO.get(name, {})
    
    # Check profile cache first (fastest)
    cache_key = name.lower()
    cached_profile = MEMBER_PROFILE_CACHE.get(cache_key)
    if cached_profile and cached_profile.get('profile_link'):
        member_id = cached_profile.get('id', 1)
        profile_link = cached_profile.get('profile_link')
        photo = member_info.get('photo', '') if member_info else cached_profile.get('photo_url', '')
    else:
        # Fallback: try database lookup
        member_id = None
        profile_link = None
        photo = ""
        
        if member_info:
            member_id = member_info.get('id')
            profile_link = member_info.get('profile_link')
            photo = member_info.get('photo', '')
        
        # If not in cache, try database
        if not profile_link and DB_MANAGER:
            try:
                db_member = DB_MANAGER.get_member_by_name(name)
                if db_member:
                    member_id = db_member.get('id')
                    profile_link = db_member.get('profile_link')
                    photo = db_member.get('photo', '')
            except:
                pass
        
        # Ensure member_id is set
        if not member_id:
            if member_info:
                member_id = member_info.get('id')
            if not member_id:
                member_id = 1
    
    # Ensure member_id is an integer
    try:
        member_id = int(member_id) if member_id else 1
    except (ValueError, TypeError):
        member_id = 1
    
    # Validate and set profile_link
    if profile_link and isinstance(profile_link, str):
        profile_link = profile_link.strip()
        if not profile_link:
            profile_link = f"/member/{member_id}"
    else:
        profile_link = f"/member/{member_id}"
    
    # Ensure profile_link is never empty
    if not profile_link:
        profile_link = f"/member/{member_id}"
    
    # Format photo URL
    photo_url = ""
    safe_name = name.replace(' ', '_').replace('/', '_').lower()
    local_photo_path = f"static/members/{safe_name}.jpg"
    
    if photo:
        if photo.startswith('/static/'):
            photo_url = photo
        elif photo.startswith('static/'):
            photo_url = "/" + photo
        elif photo.startswith('http'):
            if os.path.exists(local_photo_path):
                photo_url = f"/static/members/{safe_name}.jpg"
            else:
                photo_url = photo
        else:
            if os.path.exists(local_photo_path):
                photo_url = f"/static/members/{safe_name}.jpg"
            else:
                photo_url = photo if photo else ""
    
    # Check for local file
    if not photo_url or photo_url == "":
        if os.path.exists(local_photo_path):
            photo_url = f"/static/members/{safe_name}.jpg"
    
    # Fallback
    if not photo_url or photo_url == "":
        photo_url = f"/static/members/{safe_name}.jpg"
    
    # Build final object
    final_object = {
        "member_id": member_id,
        "name": str(name).strip() if name else "Unknown",
        "similarity_rate": float(round(similarity, 1)) if similarity else 0.0,
        "confidence_score": float(round(confidence, 1)) if confidence else 0.0,
        "photo_url": str(photo_url).strip() if photo_url else f"/static/members/{safe_name}.jpg",
        "profile_link": str(profile_link).strip()
    }
    
    # Ensure no empty strings in critical fields
    if not final_object["name"] or final_object["name"] == "None":
        final_object["name"] = "Unknown"
    if not final_object["profile_link"]:
        final_object["profile_link"] = f"/member/{final_object['member_id']}"
    
    return final_object

def find_similar_faces(image_path):
    """Compare uploaded face with database and return matches
    If > 100 members: return top 10 matches
    If <= 100 members: return top match only"""
    
    detected_gender = detect_gender_from_face_shape(image_path)
    
    result = MATCHER.find_similar_faces(
        image_path, 
        threshold=MIN_SIMILARITY_THRESHOLD,
        top_k=10
    )
    
    detection_quality = result.get("detection_quality", 0.0)
    
    if detection_quality < 0.7 and result.get("status") != "success":
        return {
            "success": False,
            "has_match": False,
            "detected_gender": detected_gender,
            "top_match": None,
            "top_matches": [],
            "message": f"Image quality issue detected. Please upload a clear face photo.",
            "detection_quality": detection_quality
        }
    
    if result.get("status") in ["error", "no_match", "warning"]:
        return {
            "success": False,
            "has_match": False,
            "detected_gender": detected_gender,
            "top_match": None,
            "top_matches": [],
            "message": result.get("message", "No match found"),
            "detection_quality": detection_quality
        }
    
    matches = result.get("matches", [])
    if not matches:
        return {
            "success": False,
            "has_match": False,
            "detected_gender": detected_gender,
            "top_match": None,
            "top_matches": [],
            "message": "No similar faces found",
            "detection_quality": detection_quality
        }
    
    # Get total members count
    stats = MATCHER.get_stats()
    total_members = stats.get('total_profiles', 0)
    
    # Determine if we should return top 10 or just top 1
    return_top_n = 10 if total_members > 100 else 1
    matches_to_process = matches[:return_top_n]
    
    print(f"[DEBUG] Total members: {total_members}, Returning top {return_top_n} matches")
    
    # Build match objects for all matches that meet threshold
    top_matches = []
    for match_data in matches_to_process:
        name = match_data['name']
        similarity = match_data['similarity']
        confidence = match_data.get('confidence', 0)
        
        # Skip if confidence is too low
        if confidence < 50:
            print(f"[SKIP] {name}: confidence too low ({confidence:.0f}%)")
            continue
        
        # Get member info from database FIRST before building match object
        member_info = {}
        if DB_MANAGER:
            try:
                db_member = DB_MANAGER.get_member_by_name(name)
                if db_member:
                    member_info = db_member
                    print(f"[DB] Found member info for {name}: ID={db_member.get('id')}, Profile={db_member.get('profile_link')}")
            except Exception as e:
                print(f"[WARN] Database lookup failed for {name}: {e}")
        
        match_obj = build_match_object(name, similarity, confidence, member_info)
        
        # Ensure all required fields exist
        required_fields = ['name', 'similarity_rate', 'photo_url', 'profile_link', 'member_id', 'confidence_score']
        if match_obj and all(k in match_obj for k in required_fields):
            # Validate data types and values
            try:
                assert isinstance(match_obj['name'], str) and match_obj['name'].strip()
                assert isinstance(match_obj['similarity_rate'], (int, float)) and 0 <= match_obj['similarity_rate'] <= 100
                assert isinstance(match_obj['photo_url'], str)
                assert isinstance(match_obj['profile_link'], str) and match_obj['profile_link'].strip()
                
                top_matches.append(match_obj)
                print(f"[MATCH] {name}: {similarity:.1f}% similarity, {confidence:.0f}% confidence, Image: {match_obj['photo_url']}")
            except (AssertionError, KeyError) as e:
                print(f"[ERROR] Match object validation failed for {name} - {e}")
        else:
            print(f"[ERROR] Match object incomplete for {name}: missing fields")
    
    if not top_matches:
        return {
            "success": False,
            "has_match": False,
            "detected_gender": detected_gender,
            "top_match": None,
            "top_matches": [],
            "message": "No matches with sufficient confidence found",
            "detection_quality": detection_quality
        }
    
    # For backward compatibility, set top_match to the first match
    top_match = top_matches[0]
    
    return {
        "success": True,
        "has_match": True,
        "detected_gender": detected_gender,
        "top_match": top_match,
        "top_matches": top_matches,  # New field with list of top matches
        "match_count": len(top_matches),
        "total_members": total_members,
        "return_top_n": return_top_n,
        "message": f"Found {len(top_matches)} match(es)" if total_members > 100 else f"Match found with {top_match['similarity_rate']:.1f}% similarity",
        "detection_quality": detection_quality
    }

# Initialize database with member profiles
db_initialized = initialize_matcher_database()
MEMBERS_INFO = load_members_info()

if not db_initialized:
    print("[!] WARNING: Matcher database initialization failed!")

# ============================================================================
# FLASK APPLICATION
# ============================================================================

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/debug/status')
def debug_status():
    """Debug endpoint to check system status"""
    try:
        stats = MATCHER.get_stats()
        
        debug_info = {
            "status": "ok",
            "database": {
                "type": "MySQL" if DB_MANAGER and not DB_MANAGER.use_sqlite else "SQLite",
                "connected": DB_MANAGER.connection is not None if DB_MANAGER else False,
                "members_loaded": stats.get('total_profiles', 0),
                "members_in_cache": len(MEMBERS_INFO),
            },
            "members_sample": list(MEMBERS_INFO.keys())[:5] if MEMBERS_INFO else [],
            "matcher": {
                "status": "initialized",
                "total_profiles": stats.get('total_profiles', 0),
                "profiles": stats.get('profiles', [])[:5]
            }
        }
        
        # Check if static/members directory exists and has images
        if os.path.exists('static/members'):
            member_images = os.listdir('static/members')
            debug_info['member_images_count'] = len(member_images)
            debug_info['member_images_sample'] = member_images[:5]
        else:
            debug_info['member_images_count'] = 0
            debug_info['member_images_sample'] = []
        
        return jsonify(debug_info), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/member/<int:member_id>')
def member_profile(member_id):
    """Display or redirect to member's profile"""
    try:
        # Try to get member from MEMBERS_INFO first (cached)
        members = None
        member = None
        
        # Search in MEMBERS_INFO first
        if MEMBERS_INFO:
            for name, info in MEMBERS_INFO.items():
                if int(info.get('id', 0)) == int(member_id):
                    member = info
                    break
        
        # If not found in cache, try directly from database
        if not member and DB_MANAGER:
            try:
                all_members = DB_MANAGER.get_all_members()
                member = next((m for m in all_members if int(m.get('id', 0)) == int(member_id)), None)
            except Exception as e:
                print(f"[ERROR] Database query failed: {e}")
        
        if not member:
            print(f"[WARN] Member with ID {member_id} not found in any source")
            return render_template('index.html'), 404
        
        profile_link = member.get('profile_link')
        
        # Log for debugging
        print(f"[DEBUG] member_profile route for ID {member_id}:")
        print(f"  - Member name: {member.get('name')}")
        print(f"  - Profile link value: {profile_link}")
        print(f"  - Profile link is truthy: {bool(profile_link)}")
        if profile_link and isinstance(profile_link, str):
            print(f"  - Profile link stripped: '{profile_link.strip()}'")
            print(f"  - Profile link length: {len(profile_link)}")
        
        # If profile_link exists and is valid, redirect to it
        # Safely check if profile_link is a non-empty string
        is_valid_external_link = (
            profile_link and 
            isinstance(profile_link, str) and 
            profile_link.strip() and 
            profile_link.strip() != f"/member/{member_id}"
        )
        
        if is_valid_external_link:
            print(f"[REDIRECT] Redirecting to: {profile_link}")
            return redirect(profile_link, code=302)
        else:
            print(f"[FALLBACK] Using fallback profile page (profile_link={profile_link})")
        
        # Otherwise, display member information on a fallback page
        name = member.get('name', 'Unknown')
        photo = member.get('photo', '')
        
        # Format photo URL for display (same logic as find_similar_faces)
        if photo:
            if photo.startswith('/static/'):
                photo_url = photo
            elif photo.startswith('static/'):
                photo_url = "/" + photo
            elif photo.startswith('http'):
                # External URL - check if we have a local copy
                safe_name = name.replace(' ', '_').replace('/', '_').lower()
                local_photo_path = f"static/members/{safe_name}.jpg"
                
                # Check if local file exists
                if os.path.exists(local_photo_path):
                    photo_url = f"/static/members/{safe_name}.jpg"
                else:
                    # Fall back to external URL if local copy doesn't exist
                    photo_url = photo
            else:
                safe_name = name.replace(' ', '_').replace('/', '_').lower()
                photo_url = f"/static/members/{safe_name}.jpg"
        else:
            photo_url = ""
        
        html = f"""
        <html>
        <head>
            <title>{name} - Profile</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 30px auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 15px rgba(0,0,0,0.1); }}
                .back-link {{ color: #3498db; text-decoration: none; margin-bottom: 20px; display: inline-block; }}
                .back-link:hover {{ text-decoration: underline; }}
                .profile-photo {{ width: 100%; max-width: 300px; border-radius: 12px; margin: 20px auto; display: block; }}
                h1 {{ color: #2c3e50; text-align: center; margin-top: 0; }}
                .info-group {{ margin: 15px 0; padding: 12px; background: #f8f9fa; border-radius: 6px; }}
                .label {{ color: #666; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
                .value {{ color: #2c3e50; font-size: 16px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-link">← Back to Home</a>
                <h1>{name}</h1>
                """
        
        if photo_url:
            html += f'<img src="{photo_url}" alt="{name}" class="profile-photo" onerror="this.style.display=\'none\'">'
        
        if member.get('age'):
            html += f'<div class="info-group"><div class="label">Age</div><div class="value">{member.get("age")}</div></div>'
        
        if member.get('gender'):
            html += f'<div class="info-group"><div class="label">Gender</div><div class="value">{member.get("gender")}</div></div>'
        
        if member.get('location'):
            html += f'<div class="info-group"><div class="label">Location</div><div class="value">{member.get("location")}</div></div>'
        
        html += """
                <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                    <p>Member Profile | Face Recognition System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html, 200
        
    except Exception as e:
        print(f"[ERROR] Member profile error: {e}")
        return render_template('index.html'), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded image and find similar faces"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file format. Allowed: JPG, JPEG, PNG, BMP'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        analysis_result = find_similar_faces(filepath)
        
        top_match = analysis_result.get("top_match")
        has_match = analysis_result.get("has_match", False)
        
        stats = MATCHER.get_stats()
        
        print(f"\n[ANALYSIS] Uploaded: {filename}")
        print(f"[ANALYSIS] Database: {stats.get('total_profiles', 0)} total profiles loaded")
        if has_match and top_match:
            print(f"[ANALYSIS] Top match: {top_match['name']} ({top_match['similarity_rate']:.1f}%)")
        else:
            print(f"[ANALYSIS] No match found")
        
        try:
            with open("face_recognition_log.txt", "a") as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if has_match and top_match:
                    f.write(f"[{timestamp}] {filename} - MATCH FOUND: {top_match['name']} ({top_match['similarity_rate']:.1f}%)\n")
                else:
                    f.write(f"[{timestamp}] {filename} - NO MATCH (threshold: {MIN_SIMILARITY_THRESHOLD}%+)\n")
        except:
            pass
        
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[WARN] Could not delete uploaded file: {filepath} ({e})")
        
        # Prepare response data
        top_matches = analysis_result.get("top_matches", [])
        total_members = analysis_result.get("total_members", stats['total_profiles'])
        return_top_n = analysis_result.get("return_top_n", 1)
        
        # Validate and clean match data
        cleaned_matches = []
        for match in top_matches:
            try:
                cleaned_match = {
                    'member_id': int(match.get('member_id', 1)),
                    'name': str(match.get('name', 'Unknown')).strip(),
                    'similarity_rate': float(match.get('similarity_rate', 0)),
                    'confidence_score': float(match.get('confidence_score', 0)),
                    'photo_url': str(match.get('photo_url', '')).strip(),
                    'profile_link': str(match.get('profile_link', '/member/1')).strip()
                }
                # Ensure all critical fields are present
                if cleaned_match['name'] and cleaned_match['photo_url'] and cleaned_match['profile_link']:
                    cleaned_matches.append(cleaned_match)
            except (ValueError, TypeError) as e:
                print(f"[WARN] Skipping malformed match data: {e}")
                continue
        
        response_data = {
            'success': 1 if analysis_result.get("success") else 0,
            'detected_gender': analysis_result.get("detected_gender", "Unknown"),
            'has_match': int(has_match),
            'top_match': cleaned_matches[0] if cleaned_matches else None,
            'top_matches': cleaned_matches,  # Include cleaned list of top matches
            'match_count': len(cleaned_matches),
            'total_members': total_members,
            'return_top_n': return_top_n,
            'uploaded_filename': filename,  # Add uploaded image filename
            'message': analysis_result.get("message", "Analysis complete")
        }
        
        # Log debug info
        print(f"[API RESPONSE] Total members: {total_members}, Returning {return_top_n} matches, Found: {len(cleaned_matches)}")
        if cleaned_matches:
            for idx, m in enumerate(cleaned_matches, 1):
                print(f"  Match {idx}: {m['name']} - {m['similarity_rate']:.1f}% - {m['photo_url']}")
        
        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("[*] FACE RECOGNITION - WEB APPLICATION")
    print("="*70)
    
    stats = MATCHER.get_stats()
    print(f"\n[OK] Database Status:")
    print(f"    Total profiles: {stats.get('total_profiles', 0)}")
    print(f"    Profiles loaded: {len(stats.get('profiles', []))}")
    print(f"\n[OK] Engine: TrustworthyFaceMatcher (Multi-feature + Ensemble)")
    print(f"[OK] Server: http://localhost:5000")
    print("\n[INFO] How it works:")
    print("  1. Upload any face image")
    print("  2. System extracts robust multi-feature embedding")
    print("  3. Performs trustworthy similarity matching")
    print("  4. Shows results ranked by confidence (65%+ threshold)")
    print("\n[*] Open http://localhost:5000 in your browser!")
    print("="*70 + "\n")
    
    app.run(debug=False, host='localhost', port=5000, use_reloader=False, threaded=False)
