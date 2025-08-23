"""
Upload API endpoints for Telegram Bot Manager v2

This module handles file uploads for bot avatars and other assets.
Provides secure file upload functionality with validation and storage.
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import hashlib

from shared.auth import api_v2_auth_required
from shared.utils import api_response

logger = logging.getLogger(__name__)

# Create uploads blueprint
api_v2_uploads_bp = Blueprint('api_v2_uploads', __name__, url_prefix='/api/v2')

# Configuration
UPLOAD_FOLDER = Path(__file__).resolve().parent.parent.parent / "static" / "uploads"
AVATAR_FOLDER = UPLOAD_FOLDER / "avatars"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'
}

def allowed_file(filename, mimetype):
    """Check if file extension and MIME type are allowed"""
    if not filename:
        return False
    
    # Check extension
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    extension_ok = extension in ALLOWED_EXTENSIONS
    
    # Check MIME type
    mime_ok = mimetype in ALLOWED_MIME_TYPES
    
    return extension_ok and mime_ok

def generate_unique_filename(original_filename, prefix="avatar"):
    """Generate unique filename with timestamp and UUID"""
    if not original_filename:
        extension = "png"
    else:
        extension = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'png'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{prefix}_{timestamp}_{unique_id}.{extension}"

def validate_and_process_image(file_path, max_width=800, max_height=600):
    """Validate and optimize uploaded image"""
    try:
        with Image.open(file_path) as img:
            # Check if image is valid
            img.verify()
        
        # Re-open for processing (verify() closes the image)
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
                logger.info(f"Resized image to {img.width}x{img.height}")
            
            return True, img.size
            
    except Exception as e:
        logger.error(f"Image validation failed: {e}")
        return False, str(e)

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of file for duplicate detection"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


@api_v2_uploads_bp.route("/upload/avatar", methods=["POST"])
@api_v2_auth_required
def upload_avatar():
    """
    Upload bot avatar image
    
    Expected: multipart/form-data with 'avatar' file field
    
    Returns:
        JSON with uploaded file URL and metadata
    """
    try:
        # Check if file was uploaded
        if 'avatar' not in request.files:
            return api_response(error="No file uploaded", status_code=400)
        
        file = request.files['avatar']
        
        # Check if file was selected
        if file.filename == '':
            return api_response(error="No file selected", status_code=400)
        
        # Check file size
        if request.content_length and request.content_length > MAX_FILE_SIZE:
            return api_response(
                error=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB", 
                status_code=400
            )
        
        # Check file type
        if not allowed_file(file.filename, file.mimetype):
            return api_response(
                error=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}", 
                status_code=400
            )
        
        # Ensure upload directory exists
        AVATAR_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        file_path = AVATAR_FOLDER / filename
        
        # Save file temporarily
        file.save(str(file_path))
        
        # Validate and process image
        is_valid, result = validate_and_process_image(str(file_path))
        if not is_valid:
            # Delete invalid file
            if file_path.exists():
                file_path.unlink()
            return api_response(error=f"Invalid image: {result}", status_code=400)
        
        # Calculate file hash for duplicate detection
        file_hash = calculate_file_hash(str(file_path))
        
        # Get file stats
        file_stats = file_path.stat()
        file_size = file_stats.st_size
        image_width, image_height = result
        
        # Generate URL for accessing the file
        file_url = f"/static/uploads/avatars/{filename}"
        
        # Prepare response data
        response_data = {
            "success": True,
            "file_url": file_url,
            "filename": filename,
            "original_filename": file.filename,
            "file_size": file_size,
            "file_hash": file_hash,
            "image_dimensions": {
                "width": image_width,
                "height": image_height
            },
            "uploaded_at": datetime.now().isoformat() + "Z",
            "mime_type": file.mimetype
        }
        
        logger.info(f"Successfully uploaded avatar: {filename} ({file_size} bytes)")
        return api_response(response_data, "Avatar uploaded successfully", status_code=201)
        
    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return api_response(error="Failed to upload avatar", status_code=500)


@api_v2_uploads_bp.route("/upload/avatar/<filename>", methods=["DELETE"])
@api_v2_auth_required
def delete_avatar(filename):
    """
    Delete uploaded avatar file
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        JSON success/error response
    """
    try:
        # Sanitize filename
        filename = secure_filename(filename)
        file_path = AVATAR_FOLDER / filename
        
        # Check if file exists
        if not file_path.exists():
            return api_response(error="File not found", status_code=404)
        
        # Delete file
        file_path.unlink()
        
        logger.info(f"Successfully deleted avatar: {filename}")
        return api_response({"filename": filename}, "Avatar deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting avatar {filename}: {e}")
        return api_response(error="Failed to delete avatar", status_code=500)


@api_v2_uploads_bp.route("/upload/info", methods=["GET"])
@api_v2_auth_required
def upload_info():
    """
    Get upload configuration and limits
    
    Returns:
        JSON with upload limits and allowed file types
    """
    try:
        info = {
            "max_file_size": MAX_FILE_SIZE,
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "allowed_mime_types": list(ALLOWED_MIME_TYPES),
            "upload_path": "/api/v2/upload/avatar",
            "max_image_dimensions": {
                "width": 800,
                "height": 600
            }
        }
        
        return api_response(info, "Upload configuration retrieved")
        
    except Exception as e:
        logger.error(f"Error getting upload info: {e}")
        return api_response(error="Failed to get upload info", status_code=500)
