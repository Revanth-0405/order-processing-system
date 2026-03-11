from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models.webhook import WebhookSubscription
from app.schemas.webhook import webhook_schema, webhooks_schema
from app.utils.decorators import jwt_required

webhooks_bp = Blueprint('webhooks', __name__)

@webhooks_bp.route('', methods=['POST'])
@jwt_required
def create_webhook():
    user_id = get_jwt_identity()
    json_data = request.get_json()

    try:
        data = webhook_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Check for duplicates to prevent spamming the same URL with the same event
    existing = WebhookSubscription.query.filter_by(
        user_id=user_id, 
        target_url=data['target_url'], 
        event_type=data['event_type']
    ).first()
    
    if existing:
        return jsonify({'message': 'Webhook already exists for this URL and event.'}), 400

    new_webhook = WebhookSubscription(
        user_id=user_id,
        target_url=data['target_url'],
        event_type=data['event_type']
    )
    db.session.add(new_webhook)
    db.session.commit()

    return jsonify(webhook_schema.dump(new_webhook)), 201

@webhooks_bp.route('', methods=['GET'])
@jwt_required
def get_webhooks():
    user_id = get_jwt_identity()
    webhooks = WebhookSubscription.query.filter_by(user_id=user_id).all()
    return jsonify(webhooks_schema.dump(webhooks)), 200

@webhooks_bp.route('/<uuid:webhook_id>', methods=['DELETE'])
@jwt_required
def delete_webhook(webhook_id):
    user_id = get_jwt_identity()
    webhook = WebhookSubscription.query.filter_by(id=webhook_id, user_id=user_id).first()
    
    if not webhook:
        return jsonify({'message': 'Webhook not found'}), 404

    db.session.delete(webhook)
    db.session.commit()
    return jsonify({'message': 'Webhook deleted successfully'}), 200