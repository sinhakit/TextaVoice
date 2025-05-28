from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  
from werkzeug.security import generate_password_hash, check_password_hash 
import re     

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///textavoice.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Audiobook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    audio_content = db.Column(db.Text, nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Password strength checker
def is_strong_password(password):
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))

# Routes
@app.route('/api/audiobooks', methods=['GET'])
def get_audiobooks():
    audiobooks = Audiobook.query.all()
    result = []
    for audiobook in audiobooks:
        result.append({
            "id": audiobook.id,
            "title": audiobook.title,
            "author": audiobook.author,
            "audio_content": audiobook.audio_content
        })
    return jsonify(result)

@app.route('/api/add_audiobook', methods=['POST'])
def add_audiobook():
    try:
        data = request.get_json()
        if 'title' not in data or 'author' not in data or 'audioUrl' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        new_audiobook = Audiobook(
            title=data['title'],
            author=data['author'],
            audio_content=data['audioUrl']
        )
        db.session.add(new_audiobook)
        db.session.commit()

        return jsonify({"message": "Audiobook added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete_audiobook/<int:audiobook_id>', methods=['DELETE'])
def delete_audiobook(audiobook_id):
    try:
        audiobook = Audiobook.query.get(audiobook_id)
        if not audiobook:
            return jsonify({"error": "Audiobook not found"}), 404

        db.session.delete(audiobook)
        db.session.commit()
        return jsonify({"message": "Audiobook deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if not is_strong_password(password):
        return jsonify({
            "error": "Password must be at least 8 characters, include 1 uppercase letter, 1 number, and 1 special character."
        }), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401
    
@app.route('/api/logout', methods=['POST'])
def logout():
    # In session-based auth, you'd do: session.clear()
    # But since no session/token used, just return success
    return jsonify({"message": "Logout successful"}), 200


if __name__ == "__main__":
    app.run(debug=True)
