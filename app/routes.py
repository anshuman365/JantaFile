from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from app import db
from app.models import Episode, SharedData, Subscription
from app.utils.security import SecurityUtils
from app.utils.analysis import DocumentAnalyzer
import os
from io import BytesIO
from flask import current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# Initialize Limiter
limiter = Limiter(key_func=get_remote_address, app=None)

bp = Blueprint('main', __name__)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/process')
def process():
    return render_template('process.html')

@bp.route('/faq')
def faq():
    return render_template('faq.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/search')
def search():
    return render_template('search.html')

@bp.route('/')
def index():
    episodes = Episode.query.order_by(Episode.created_at.desc()).limit(3).all()
    return render_template('index.html', episodes=episodes)

@bp.route('/episodes')
def episodes():
    return render_template('episodes.html')

@bp.route('/api/episodes')
def api_episodes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    episodes_pagination = Episode.query.paginate(page=page, per_page=per_page, error_out=False)

    episodes_data = [e.serialize() for e in episodes_pagination.items]

    return jsonify({
        'episodes': episodes_data,
        'page': episodes_pagination.page,
        'pages': episodes_pagination.pages,
        'total': episodes_pagination.total,
        'has_next': episodes_pagination.has_next,
        'has_prev': episodes_pagination.has_prev
    })

@bp.route('/api/search')
def search_api():
    all_episodes = Episode.query.all()
    return jsonify([e.serialize() for e in all_episodes])

@bp.route('/share-data', methods=['GET', 'POST'])
def submit_shared_data():
    if request.method == 'GET':
        form_data = {
            'hidden_tag': lambda: '',
            'title': request.form.get('title', ''),
            'description': request.form.get('description', '')
        }
        return render_template('share_data.html', form=form_data)
    if request.method == 'POST':
        submission_code = SecurityUtils.generate_submission_code()
        new_submission = SharedData(
            title=request.form.get('title'),
            description=request.form.get('description'),
            submission_code=submission_code,
            ip_hash=SecurityUtils.hash_ip(request.remote_addr)
        )
        db.session.add(new_submission)
        db.session.commit()
        return jsonify({'code': submission_code})

@bp.route('/submit-data', methods=['POST'])
@limiter.limit("5 per minute")
def submit_data():
    files = request.files.getlist('files')

    if not files:
        return jsonify({'error': 'No files selected. Please upload at least one file.'}), 400

    description = request.form.get('description')
    if not description or not description.strip():
        return jsonify({'error': 'Description is required.'}), 400

    encryption_key = os.getenv('ENCRYPTION_KEY')

    print(f"DEBUG (routes.py): Raw ENCRYPTION_KEY from os.getenv: '{encryption_key}'")
    print(f"DEBUG (routes.py): Type of ENCRYPTION_KEY: {type(encryption_key)}")
    if encryption_key:
        print(f"DEBUG (routes.py): Length of ENCRYPTION_KEY: {len(encryption_key)}")
        print(f"DEBUG (routes.py): ENCRYPTION_KEY ends with '=': {encryption_key.endswith('=')}")
        print(f"DEBUG (routes.py): ENCRYPTION_KEY contains whitespace: {' ' in encryption_key or '\\n' in encryption_key or '\\r' in encryption_key}")

    if not encryption_key:
        return jsonify({'error': 'Encryption key not configured on the server. Please set the ENCRYPTION_KEY environment variable.'}), 500
    
    try:
        Fernet(encryption_key.encode('utf-8'))
    except Exception as e:
        return jsonify({'error': f'Invalid ENCRYPTION_KEY format. Ensure it is a valid Fernet key. Details: {e}'}), 500

    encrypted_files = []

    for file in files:
        if not file.filename or not SecurityUtils.allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type or filename missing for one of the uploaded files.'}), 400

        file_content = file.read()
        if len(file_content) > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': f'File "{file.filename}" size exceeds limit ({current_app.config["MAX_CONTENT_LENGTH"] / (1024*1024):.0f}MB).'}), 400

        file_stream = BytesIO(file_content)
        try:
            sanitized_content_bytes = DocumentAnalyzer.sanitize_metadata(file_stream, file.filename)
        except Exception as e:
            return jsonify({'error': f'Failed to sanitize metadata for {file.filename}: {str(e)}'}), 500

        try:
            encrypted_data = SecurityUtils.encrypt_symmetric(sanitized_content_bytes)
        except ValueError as e:
            return jsonify({'error': f'Encryption setup error for {file.filename}: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'An unexpected error occurred during encryption for {file.filename}: {str(e)}'}), 500

        filename = SecurityUtils.sanitize_filename(file.filename)
        file_hash = DocumentAnalyzer.calculate_document_hash(sanitized_content_bytes)
        save_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            f"{file_hash}_{filename}.encrypted"
        )
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        with open(save_path, 'wb') as f:
            f.write(encrypted_data)

        encrypted_files.append(save_path)

    # NEW: Handle optional contact method and info
    contact_method = request.form.get('contact_method')
    contact_info = request.form.get('contact_info', '')
    
    encrypted_contact_b64_string = None
    if contact_info and contact_method: # Only encrypt if both method and info are provided
        try:
            encrypted_contact_bytes = SecurityUtils.encrypt_symmetric(contact_info.encode('utf-8'))
            encrypted_contact_b64_string = SecurityUtils.bytes_to_base64_string(encrypted_contact_bytes)
        except ValueError as e:
            return jsonify({'error': f'Encryption setup error for contact info: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'An unexpected error occurred during encryption for contact info: {str(e)}'}), 500
    elif contact_info and not contact_method:
        return jsonify({'error': 'Contact information provided, but no contact method selected.'}), 400
    elif not contact_info and contact_method:
        return jsonify({'error': 'Contact method selected, but no contact information provided.'}), 400


    submission = SharedData(
        title=request.form.get('title', ''),
        description=description,
        files=encrypted_files,
        contact_method=contact_method, # Store the selected contact method
        contact=encrypted_contact_b64_string, # Store base64 encoded string (can be None)
        submission_code=SecurityUtils.generate_submission_code(),
        ip_hash=SecurityUtils.hash_ip(request.remote_addr)
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'code': submission.submission_code
    }), 201

@bp.route('/episodes/<int:episode_id>')
def episode_detail(episode_id):
    episode = Episode.query.get_or_404(episode_id)
    return render_template('episode_detail.html', episode=episode)

@bp.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@bp.route('/health')
def health_check():
    return "OK", 200

@bp.route('/subscribe', methods=['POST'])
def subscribe():
    subscription = request.get_json()
    sub = Subscription(
        endpoint=subscription['endpoint'],
        keys=json.dumps(subscription['keys'])
    )
    db.session.add(sub)
    db.session.commit()
    return jsonify({'success': True})