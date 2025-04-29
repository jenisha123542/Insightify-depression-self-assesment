from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import pickle
import os

# Load the model
with open('models/depression_model.pkl', 'rb') as file:
    model = pickle.load(file)

user_bp = Blueprint("user", __name__, "/")

# Database configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "insightify"
}

# Static routes
@user_bp.route('/')
def index():
    return render_template('index.html')



@user_bp.route('/about')
def about():
    return render_template('about.html')

@user_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (name, email, content)
                VALUES (%s, %s, %s)
            """, (name, email, message))

            conn.commit()

            # Flash success message and redirect to the same contact page
            flash("Your message has been sent successfully!", "success")
            return redirect(url_for('user.contact'))

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash("Error saving your message. Please try again.", "error")
            return redirect(url_for('user.contact'))
        finally:
            if conn:
                conn.close()

    return render_template('contact.html')

@user_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@user_bp.route('/terms')
def terms():
    return render_template('terms.html')

# Authentication routes
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400
            
        fullname = data.get('fullname', '').strip()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')

        if not all([fullname, email, password]):
            return jsonify({'success': False, 'message': 'All fields are required!'}), 400

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already exists!'}), 400
            
        hashed_pw = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (fullname, email, password) VALUES (%s, %s, %s)",
            (fullname, email, hashed_pw)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Signup successful!'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received'}), 400
        
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'All fields required!'}), 400

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, fullname, email, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            return jsonify({
                'success': True,
                'message': 'Login successful!',
                'user': {
                    'id': user['id'],
                    'fullname': user['fullname'],
                    'email': user['email']
                }
            }), 200
        return jsonify({'success': False, 'message': 'Invalid credentials!'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@user_bp.route('/logout')
def logout():
    return jsonify({'success': True}), 200

@user_bp.route('/contact', methods=['GET', 'POST'], endpoint='user_contact')
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Now, insert this data into the MySQL database
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO messages (name, email, content)
                VALUES (%s, %s, %s)
            """, (name, email, message))

            conn.commit()
            
            return redirect(url_for('user.contact'))  # Correct the redirect URL
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return "Error saving your message", 500
        finally:
            if conn:
                conn.close()
    return render_template('contact.html')

@user_bp.route('/test')
def test():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Get all questions
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()

        # Get all options
        question_ids = [q['id'] for q in questions]
        format_strings = ','.join(['%s'] * len(question_ids))
        cursor.execute(f"SELECT * FROM options WHERE question_id IN ({format_strings})", tuple(question_ids))
        options = cursor.fetchall()

        # Group options by question_id
        from collections import defaultdict
        options_dict = defaultdict(list)
        for opt in options:
            options_dict[opt['question_id']].append(opt)

        return render_template('test.html', questions=questions, options=options_dict)

    except Exception as e:
        return f"Error loading test: {str(e)}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@user_bp.route('/submit_test', methods=['POST'])
def submit_test():
    try:
        # Collect answers from the submitted form
        answers = {key: int(value) for key, value in request.form.items() if key.startswith("q")}
        total_score = sum(answers.values())
        
        # Optional: You could save the answers and score to the database here
        
        # Decide result based on score (basic logic)
        if total_score <= 4:
            result = "Minimal or no depression"
        elif total_score <= 9:
            result = "Mild depression"
        elif total_score <= 14:
            result = "Moderate depression"
        elif total_score <= 19:
            result = "Moderately severe depression"
        else:
            result = "Severe depression"

        return render_template('result.html', score=total_score, result=result)
    
    except Exception as e:
        return f"An error occurred: {str(e)}"


@user_bp.route('/predict', methods=['POST'])
def predict_depression():
    try:
        data = request.get_json()
        total_score = data.get('total_score')

        if total_score is None:
            return jsonify({'error': 'Total score not provided'}), 400

        prediction = model.predict([[total_score]])  # model is already loaded
        result = prediction[0]

        return jsonify({'prediction': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500




# if __name__ == '__main__':
#     user_bp.run(debug=True, host='0.0.0.0', port=5000)
