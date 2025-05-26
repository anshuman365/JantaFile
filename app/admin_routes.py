from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Episode, SharedData, Subscription
from app.utils.analysis import DocumentAnalyzer
from app.utils.security import SecurityUtils
from datetime import datetime
import os
from io import BytesIO
from functools import wraps
from pywebpush import webpush, WebPushException
import json
import os
from app.utils.notifications import send_push_notification

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have administrative privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Dashboard ---
@bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard to list all episodes."""
    episodes = Episode.query.order_by(Episode.created_at.desc()).all()
    return render_template('admin/dashboard.html', episodes=episodes)

@bp.route('/episodes/add', methods=['GET', 'POST'])
@admin_required
def add_episode():
    """Route to add a new episode."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        youtube_id = request.form.get('youtube_id')
        tags_str = request.form.get('tags')
        
        if not title or not description or not youtube_id:
            flash('Title, Description, and YouTube ID are required.', 'danger')
            return redirect(url_for('admin.add_episode'))
        
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        encrypted_docs_paths = []
        
        if 'encrypted_docs_files' in request.files:
            files = request.files.getlist('encrypted_docs_files')
            for file in files:
                if file.filename and SecurityUtils.allowed_file(file.filename):
                    file_content = file.read()
                    if len(file_content) > current_app.config['MAX_CONTENT_LENGTH']:
                        flash(f'File "{file.filename}" size exceeds limit.', 'danger')
                        continue
                    file_stream = BytesIO(file_content)
                    try:
                        sanitized_content_bytes = DocumentAnalyzer.sanitize_metadata(file_stream, file.filename)
                        encrypted_data = SecurityUtils.encrypt_symmetric(sanitized_content_bytes)
                        filename = SecurityUtils.sanitize_filename(file.filename)
                        file_hash = DocumentAnalyzer.calculate_document_hash(sanitized_content_bytes)
                        save_path = os.path.join(
                            current_app.config['UPLOAD_FOLDER'],
                            f"{file_hash}_{filename}.encrypted"
                        )
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(encrypted_data)
                        encrypted_docs_paths.append(save_path)
                    except Exception as e:
                        flash(f'Error processing file {file.filename}: {str(e)}', 'danger')
                        current_app.logger.error(f"Error processing admin file upload: {e}")
                else:
                    if file.filename:
                        flash(f'Invalid file type for {file.filename}.', 'danger')
        
        combined_content = f"{title}\n{description}".encode('utf-8')
        content_hash = DocumentAnalyzer.calculate_document_hash(combined_content)
        new_episode = Episode(
            title=title,
            description=description,
            youtube_id=youtube_id,
            tags=tags,
            encrypted_docs=encrypted_docs_paths,
            content_hash=content_hash,
            is_verified=True
        )
        db.session.add(new_episode)
        db.session.commit()
        
        # Send notification after commit
        send_push_notification(
            title="New Episode Released",
            message=f"{new_episode.title} - {new_episode.description[:100]}...",
            url=f"/episodes/{new_episode.id}"
        )
        
        flash('Episode added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/episode_form.html', episode=None, form_action=url_for('admin.add_episode'))

# --- Edit Existing Episode ---
@bp.route('/episodes/edit/<int:episode_id>', methods=['GET', 'POST'])
@admin_required
def edit_episode(episode_id):
    """Route to edit an existing episode."""
    episode = Episode.query.get_or_404(episode_id)

    if request.method == 'POST':
        episode.title = request.form.get('title')
        episode.description = request.form.get('description')
        episode.youtube_id = request.form.get('youtube_id')
        tags_str = request.form.get('tags')
        
        if not episode.title or not episode.description or not episode.youtube_id:
            flash('Title, Description, and YouTube ID are required.', 'danger')
            return redirect(url_for('admin.edit_episode', episode_id=episode.id))

        episode.tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []

        if 'encrypted_docs_files' in request.files:
            files = request.files.getlist('encrypted_docs_files')
            current_encrypted_docs = episode.encrypted_docs if episode.encrypted_docs else []
            for file in files:
                if file.filename and SecurityUtils.allowed_file(file.filename):
                    file_content = file.read()
                    if len(file_content) > current_app.config['MAX_CONTENT_LENGTH']:
                        flash(f'File "{file.filename}" size exceeds limit.', 'danger')
                        continue
                    
                    file_stream = BytesIO(file_content)
                    try:
                        sanitized_content_bytes = DocumentAnalyzer.sanitize_metadata(file_stream, file.filename)
                        encrypted_data = SecurityUtils.encrypt_symmetric(sanitized_content_bytes)
                        
                        filename = SecurityUtils.sanitize_filename(file.filename)
                        file_hash = DocumentAnalyzer.calculate_document_hash(sanitized_content_bytes)
                        save_path = os.path.join(
                            current_app.config['UPLOAD_FOLDER'],
                            f"{file_hash}_{filename}.encrypted"
                        )
                        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(encrypted_data)
                        
                        current_encrypted_docs.append(save_path)
                    except Exception as e:
                        flash(f'Error processing file {file.filename}: {str(e)}', 'danger')
                        current_app.logger.error(f"Error processing admin file upload during edit: {e}")
                else:
                    if file.filename:
                        flash(f'Invalid file type for {file.filename}.', 'danger')
            episode.encrypted_docs = current_encrypted_docs

        combined_content = f"{episode.title}\n{episode.description}".encode('utf-8')
        episode.content_hash = DocumentAnalyzer.calculate_document_hash(combined_content)

        db.session.commit()
        flash('Episode updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/episode_form.html', episode=episode, form_action=url_for('admin.edit_episode', episode_id=episode.id))

# --- Delete Episode ---
@bp.route('/episodes/delete/<int:episode_id>', methods=['POST'])
@admin_required
def delete_episode(episode_id):
    """Route to delete an episode."""
    episode = Episode.query.get_or_404(episode_id)
    
    if episode.encrypted_docs:
        for file_path in episode.encrypted_docs:
            full_path = os.path.join(current_app.root_path, file_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    current_app.logger.info(f"Deleted file: {full_path}")
                except OSError as e:
                    current_app.logger.error(f"Error deleting file {full_path}: {e}")

    db.session.delete(episode)
    db.session.commit()
    flash('Episode deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# --- View All Shared Data Submissions ---
@bp.route('/shared-data')
@admin_required
def view_shared_data():
    """Admin view to list all shared data submissions."""
    shared_data_entries = SharedData.query.order_by(SharedData.submitted_at.desc()).all()
    
    for entry in shared_data_entries:
        entry.decrypted_contact = 'N/A'
        if entry.contact and entry.contact_method:
            try:
                encrypted_contact_bytes = SecurityUtils.base64_string_to_bytes(entry.contact)
                decrypted_contact_bytes = SecurityUtils.decrypt_symmetric(encrypted_contact_bytes)
                entry.decrypted_contact = decrypted_contact_bytes.decode('utf-8')
            except Exception as e:
                entry.decrypted_contact = f'[Decryption Error: {e}]'
                current_app.logger.error(f"Error decrypting shared data contact for ID {entry.id}: {e}")
        elif entry.contact and not entry.contact_method:
            entry.decrypted_contact = '[Contact info provided, but method missing]'
        elif not entry.contact and entry.contact_method:
            entry.decrypted_contact = '[Method provided, but no contact info]'

    return render_template('admin/shared_data.html', shared_data_entries=shared_data_entries)

# --- View Single Shared Data Detail ---
@bp.route('/shared-data/<int:data_id>')
@admin_required
def view_shared_data_detail(data_id):
    """Admin view to display details of a single shared data submission."""
    entry = SharedData.query.get_or_404(data_id)

    # Decrypt contact information for display
    entry.decrypted_contact = 'N/A'
    if entry.contact and entry.contact_method:
        try:
            encrypted_contact_bytes = SecurityUtils.base64_string_to_bytes(entry.contact)
            decrypted_contact_bytes = SecurityUtils.decrypt_symmetric(encrypted_contact_bytes)
            entry.decrypted_contact = decrypted_contact_bytes.decode('utf-8')
        except Exception as e:
            entry.decrypted_contact = f'[Decryption Error: {e}]'
            current_app.logger.error(f"Error decrypting shared data contact for ID {entry.id} on detail page: {e}")
    elif entry.contact and not entry.contact_method:
        entry.decrypted_contact = '[Contact info provided, but method missing]'
    elif not entry.contact and entry.contact_method:
        entry.decrypted_contact = '[Method provided, but no contact info]'

    return render_template('admin/shared_data_detail.html', entry=entry)

# --- Serve Decrypted Encrypted File ---
@bp.route('/serve-decrypted-file/<string:file_hash>/<string:original_filename>')
@admin_required
def serve_decrypted_file(file_hash, original_filename):
    """Serves decrypted files with proper security headers"""
    sanitized_original_filename = SecurityUtils.sanitize_filename(original_filename)
    encrypted_file_on_disk = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        f"{file_hash}_{sanitized_original_filename}.encrypted"
    )

    if not os.path.exists(encrypted_file_on_disk):
        abort(404, description="File not found")

    try:
        with open(encrypted_file_on_disk, 'rb') as f:
            encrypted_content = f.read()
        
        decrypted_content = SecurityUtils.decrypt_symmetric(encrypted_content)
        
        # Validate PDF magic number
        if not decrypted_content.startswith(b'%PDF-'):
            raise ValueError("Decrypted content is not a valid PDF")

        response = send_file(
            BytesIO(decrypted_content),
            mimetype='application/pdf',
            as_attachment=False,
            download_name=original_filename
        )

        # Security headers configuration
        response.headers.extend({
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'",
            'X-Permitted-Cross-Domain-Policies': 'none'
        })
        
        # Remove problematic headers
        response.headers.pop('X-Frame-Options', None)
        response.headers.pop('Content-Disposition', None)
        
        return response

    except Exception as e:
        current_app.logger.error(f"File serving error: {e}")
        abort(500, description=f"Error processing file: {str(e)}")


