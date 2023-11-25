import sqlite3
from ariadne import ObjectType, QueryType, load_schema_from_path, make_executable_schema
from ariadne import graphql_sync
from ariadne.asgi import GraphQL
from uvicorn import run

# Load the GraphQL schema from a file
type_defs = load_schema_from_path("museum.graphql")

# Define GraphQL types
query = QueryType()
room_access_type = ObjectType("RoomAccess")
db_audit_type = ObjectType("DBAudit")

# Define GraphQL queries
@query.field("allRoomAccesses")
def resolve_all_room_accesses(_, info):
    conn = sqlite3.connect('museum.db')
    c = conn.cursor()
    c.execute('SELECT employees.full_name, rooms.name, accesses.in_datetime, accesses.out_datetime FROM accesses INNER JOIN rooms ON accesses.id_room = rooms.id INNER JOIN employees ON accesses.id_employee = employees.id')
    all_room_accesses = []
    for row in c.fetchall():
        all_room_accesses.append({
            "employeeName": row[0],
            "roomName": row[1],
            "inDatetime": row[2],
            "outDatetime": row[3]
        })
    conn.close()
    return all_room_accesses

@query.field("allDBAuditLines")
def resolve_all_db_audit_lines(_, info):
    conn = sqlite3.connect('museum.db')
    c = conn.cursor()
    c.execute('SELECT * FROM db_audit')
    all_db_audit = []
    for row in c.fetchall():
        all_db_audit.append({
            "id": row[0],
            "creation_datetime": row[1],
            "sql_statement": row[2]
        })
    conn.close()
    return all_db_audit

# Create an executable GraphQL schema
schema = make_executable_schema(type_defs, [query, room_access_type, db_audit_type])

# Create a GraphQL app
app = GraphQL(schema, debug=True)

if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8000)
