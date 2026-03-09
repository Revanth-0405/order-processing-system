from flask import Blueprint, jsonify
from app.services.dynamodb_service import DynamoDBService
from app.utils.decorators import admin_required

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['GET'])
@admin_required
def list_all_events():
    # Fetching all events from DynamoDB (Note: unpaginated for local dev simplicity)
    events = DynamoDBService.get_all_events()
    return jsonify({
        'items': events,
        'total': len(events)
    }), 200

@events_bp.route('/types/<string:event_type>', methods=['GET'])
@admin_required
def get_events_by_type(event_type):
    # Queries the Global Secondary Index (GSI)
    events = DynamoDBService.get_events_by_type(event_type)
    return jsonify({
        'items': events,
        'total': len(events)
    }), 200