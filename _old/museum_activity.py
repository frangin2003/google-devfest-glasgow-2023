from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect('police_reports.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route to get a list of employees
@app.route('/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Employees')
    employees = cursor.fetchall()
    conn.close()
    return jsonify({'employees': [dict(employee) for employee in employees]})

# Route to get a list of room accesses
@app.route('/room-access', methods=['GET'])
def get_room_accesses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM RoomAccess')
    room_accesses = cursor.fetchall()
    conn.close()
    return jsonify({'room_accesses': [dict(room_access) for room_access in room_accesses]})

# Route to add a new employee
@app.route('/employees', methods=['POST'])
def add_employee():
    data = request.get_json()
    if 'name' in data and 'role' in data:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Employees (name, role) VALUES (?, ?)", (data['name'], data['role']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Employee added successfully'}), 201
    else:
        return jsonify({'error': 'Invalid data'}), 400

# Route to add a new room access
@app.route('/room-access', methods=['POST'])
def add_room_access():
    data = request.get_json()
    if 'employee_id' in data and 'room' in data and 'timestamp' in data and 'comment' in data:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO RoomAccess (employee_id, room, timestamp, comment) VALUES (?, ?, ?, ?)", (data['employee_id'], data['room'], data['timestamp'], data['comment']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Room access added successfully'}), 201
    else:
        return jsonify({'error': 'Invalid data'}), 400

if __name__ == '__main__':
    app.run(debug=True)
