"""
Authentication routes for AI Accountability Bot
"""
import os
import logging
import requests
from urllib.parse import urljoin
from flask import Blueprint, redirect, session, url_for, jsonify, request, current_app
from requests_oauthlib import OAuth2Session
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub OAuth settings
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'

auth_bp = Blueprint('auth', __name__)

def get_github_oauth():
    """Get GitHub OAuth session"""
    if not GITHUB_CLIENT_ID:
        raise ValueError("GITHUB_CLIENT_ID not found in environment variables")
    
    redirect_uri = os.getenv('GITHUB_REDIRECT_URI')
    if not redirect_uri:
        # Fallback to constructing the redirect URI
        redirect_uri = url_for('auth.github_callback', _external=True)
    
    logger.info(f"Initializing GitHub OAuth with redirect URI: {redirect_uri}")
    return OAuth2Session(
        GITHUB_CLIENT_ID,
        redirect_uri=redirect_uri,
        scope=['repo', 'user']
    )

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'github_token' not in session:
            logger.warning("Unauthenticated access attempt")
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'login_url': url_for('auth.login', _external=True)
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login')
def login():
    """Start GitHub OAuth flow"""
    try:
        github = get_github_oauth()
        authorization_url, state = github.authorization_url(GITHUB_AUTHORIZE_URL)
        session['oauth_state'] = state
        logger.info(f"Starting OAuth flow, redirecting to: {authorization_url}")
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error starting OAuth flow: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start GitHub authentication. Please try again.'
        }), 500

@auth_bp.route('/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    try:
        if 'error' in request.args:
            error_msg = request.args.get('error_description', request.args.get('error'))
            logger.error(f"GitHub OAuth error: {error_msg}")
            return jsonify({
                'status': 'error',
                'message': f'GitHub authentication failed: {error_msg}'
            }), 400

        code = request.args.get('code')
        if not code:
            logger.error("No code in GitHub callback")
            return jsonify({
                'status': 'error',
                'message': 'No authorization code received from GitHub'
            }), 400

        # Exchange code for token directly using requests
        response = requests.post(
            GITHUB_TOKEN_URL,
            headers={
                'Accept': 'application/json'
            },
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': os.getenv('GITHUB_REDIRECT_URI') or url_for('auth.github_callback', _external=True)
            }, 
        timeout=60)

        if response.status_code != 200:
            logger.error(f"GitHub token exchange failed: {response.text}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to exchange GitHub code for token'
            }), 500

        token_data = response.json()
        if 'error' in token_data:
            logger.error(f"GitHub token error: {token_data.get('error_description', token_data['error'])}")
            return jsonify({
                'status': 'error',
                'message': f"GitHub token error: {token_data.get('error_description', token_data['error'])}"
            }), 400

        # Store the token
        session['github_token'] = {
            'access_token': token_data['access_token'],
            'token_type': token_data.get('token_type', 'bearer'),
            'scope': token_data.get('scope', '').split(',')
        }
        
        logger.info("Successfully obtained GitHub token")
        return redirect(url_for('home', _external=True))
        
    except Exception as e:
        logger.error(f"Error in GitHub callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to complete GitHub authentication. Please try again.'
        }), 500

@auth_bp.route('/logout')
def logout():
    """Log out user"""
    session.pop('github_token', None)
    logger.info("User logged out")
    return redirect(url_for('home', _external=True))

@auth_bp.route('/status')
def auth_status():
    """Check authentication status"""
    is_authenticated = 'github_token' in session
    logger.debug(f"Auth status check: {'authenticated' if is_authenticated else 'not authenticated'}")
    return jsonify({
        'authenticated': is_authenticated
    })
