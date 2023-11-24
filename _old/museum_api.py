from ariadne import ObjectType, QueryType, make_executable_schema
from ariadne import graphql_sync
from ariadne.asgi import GraphQL
from uvicorn import run

# Define GraphQL types
query = QueryType()
room_access_type = ObjectType("RoomAccess")
db_audit_type = ObjectType("DBAudit")

# Define GraphQL queries
@query.field("allRoomAccesses")
def resolve_all_room_accesses(_, info):
    # Replace this with your code to fetch room access data from the database
    # and return it as a list of dictionaries with all the details
    room_accesses = [
        {"id": 1, "roomName": "Toilet", "employeeName": "Grafcuel Graeme", "inDatetime": "2023-11-24 11:59:59", "outDatetime": "2023-11-24 12:00:01"},
        # Add more room access data here
    ]
    return room_accesses

@query.field("allDBAuditLines")
def resolve_all_db_audit_lines(_, info):
    # Replace this with your code to fetch DB audit data from the database
    # and return it as a list of dictionaries with all the details
    db_audit_lines = [
        {"id": 1, "creationDatetime": "2023-11-24 09:00:00", "sqlStatement": "INSERT statement"},
        # Add more DB audit data here
    ]
    return db_audit_lines

# Create an executable GraphQL schema
schema = make_executable_schema(type_defs, [query, room_access_type, db_audit_type])

# Create a GraphQL app
app = GraphQL(schema, debug=True)

if __name__ == "__main__":
    run(app, host="127.0.0.1", port=8000)