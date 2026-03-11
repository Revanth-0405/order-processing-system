from marshmallow import Schema, fields, validate

# The list of valid events users can subscribe to
VALID_EVENTS = [
    'order_created', 'payment_success', 'payment_failed', 
    'order_confirmed', 'order_cancelled', 'inventory_updated', 
    'inventory_update_failed', 'all'
]

class WebhookSubscriptionSchema(Schema):
    id = fields.UUID(dump_only=True)
    target_url = fields.URL(required=True, error_messages={"invalid": "Must be a valid URL."})
    event_type = fields.String(required=True, validate=validate.OneOf(VALID_EVENTS))
    is_active = fields.Boolean(load_default=True)
    created_at = fields.DateTime(dump_only=True)

webhook_schema = WebhookSubscriptionSchema()
webhooks_schema = WebhookSubscriptionSchema(many=True)