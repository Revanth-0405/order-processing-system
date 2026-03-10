import json
from flask import Blueprint, jsonify, request
from app.services.dynamodb_service import DynamoDBService
from app.utils.decorators import admin_required

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['GET'])
@admin_required
def list_all_events():
    limit = request.args.get('limit', 10, type=int)
    last_key_str = request.args.get('last_key')
    
    exclusive_start_key = None
    if last_key_str:
        try:
            exclusive_start_key = json.loads(last_key_str)
        except json.JSONDecodeError:
            return jsonify({'message': 'Invalid last_key format'}), 400

    result = DynamoDBService.get_all_events(limit, exclusive_start_key)
    
    return jsonify({
        'items': result['items'],
        'next_page_key': json.dumps(result['last_evaluated_key']) if result['last_evaluated_key'] else None
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

