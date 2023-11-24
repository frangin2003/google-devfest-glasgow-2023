from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect("police.db")
    conn.row_factory = sqlite3.Row
    return conn

# Endpoint to get all cases
@app.route('/cases', methods=['GET'])
def get_cases():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases")
    cases = cursor.fetchall()
    conn.close()
    return jsonify([dict(case) for case in cases])


# API endpoint to get a single case by ID
@app.route('/cases/<int:id>', methods=['GET'])
def get_case(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE id = ?", (id,))
    case = cursor.fetchone()
    conn.close()

    if case is None:
        return jsonify({"message": "Case not found"}), 404
    return jsonify(dict(case))



# Endpoint to get all reports with associated information
@app.route('/reports', methods=['GET'])
def get_reports():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reports.*, report_types.type, suspects.full_name
        FROM reports
        JOIN report_types ON reports.id_report_type = report_types.id
        JOIN suspects ON reports.id_suspect = suspects.id
    """)
    reports = cursor.fetchall()
    conn.close()
    return jsonify([dict(report) for report in reports])

# Endpoint to get reports by type with associated information
@app.route('/reports/<report_type>', methods=['GET'])
def get_reports_by_type(report_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT reports.*, report_types.type, suspects.full_name
        FROM reports
        JOIN report_types ON reports.id_report_type = report_types.id
        JOIN suspects ON reports.id_suspect = suspects.id
        WHERE report_types.type = ?
    """, (report_type,))
    reports = cursor.fetchall()
    conn.close()
    return jsonify([dict(report) for report in reports])

# Endpoint to insert a report
@app.route('/reports', methods=['POST'])
def insert_report():
    data = request.get_json()
    id_case = data['id_case']
    id_report_type = data['id_report_type']
    id_agent = data['id_agent']
    id_suspect = data['id_suspect']
    report_content = data['report_content']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (creation_datetime, id_case, id_report_type, id_agent, id_suspect, report_content)
        VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
    """, (id_case, id_report_type, id_agent, id_suspect, report_content))
    conn.commit()
    conn.close()
    return jsonify({"message": "Report inserted successfully"}), 201

if __name__ == '__main__':
    app.run(debug=True)
