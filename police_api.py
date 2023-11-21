from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Define a function to connect to the database
def connect_db():
    conn = sqlite3.connect('police.db')
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Endpoint to get a list of all policemen
@app.route('/policemen', methods=['GET'])
def get_policemen():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Policemen')
    policemen = cursor.fetchall()
    conn.close()
    return jsonify({'policemen': [dict(policeman) for policeman in policemen]})

# Endpoint to get details of a specific policeman by policeman_id
@app.route('/policemen/<int:policeman_id>', methods=['GET'])
def get_policeman(policeman_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Policemen WHERE policeman_id = ?', (policeman_id,))
    policeman = cursor.fetchone()
    conn.close()
    if policeman:
        return jsonify(dict(policeman))
    else:
        return jsonify({'error': 'Policeman not found'}), 404

# Endpoint to get details of a specific case with suspects, policeman, and grade
@app.route('/cases/<int:case_id>', methods=['GET'])
def get_case_details(case_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Get case details
    cursor.execute('SELECT * FROM Cases WHERE case_id = ?', (case_id,))
    case = cursor.fetchone()

    if not case:
        conn.close()
        return jsonify({'error': 'Case not found'}), 404

    # Get suspects for the case
    cursor.execute('SELECT * FROM Suspects WHERE date_created = ?', (case['date_created'],))
    suspects = cursor.fetchall()

    # Get policeman assigned to the case
    cursor.execute('''
        SELECT P.*, PG.grade
        FROM Policemen AS P
        JOIN CasePolicemen AS CP ON P.policeman_id = CP.policeman_id
        JOIN PolicemenGrade AS PG ON P.rank = PG.grade
        WHERE CP.case_id = ?
    ''', (case_id,))
    policeman = cursor.fetchone()

    conn.close()

    if not policeman:
        conn.close()
        return jsonify({'error': 'Policeman not found for this case'}), 404

    # Create a dictionary with all the information
    case_details = {
        'case': dict(case),
        'suspects': [dict(suspect) for suspect in suspects],
        'policeman': dict(policeman),
    }

    return jsonify(case_details)

# Endpoint to create a new case
@app.route('/cases', methods=['POST'])
def create_case():
    data = request.get_json()
    case_number = data.get('case_number')
    details = data.get('details')
    date_created = data.get('date_created')

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Cases (case_number, details, date_created) VALUES (?, ?, ?)', (case_number, details, date_created))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Case created successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)