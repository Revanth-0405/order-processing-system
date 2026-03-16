from marshmallow import Schema, fields, validate

class OrderItemInputSchema(Schema):
    product_id = fields.UUID(required=True)
    quantity = fields.Integer(required=True, validate=validate.Range(min=1))

class OrderInputSchema(Schema):
    shipping_address = fields.String(required=True)
    notes = fields.String(allow_none=True)
    items = fields.List(fields.Nested(OrderItemInputSchema), required=True, validate=validate.Length(min=1))

class OrderItemOutputSchema(Schema):
    id = fields.UUID()
    product_id = fields.UUID()
    quantity = fields.Integer()
    unit_price = fields.Decimal(as_string=True)
    subtotal = fields.Decimal(as_string=True)

class OrderOutputSchema(Schema):
    id = fields.UUID()
    order_number = fields.String()
    user_id = fields.UUID()
    status = fields.String()
    total_amount = fields.Decimal(as_string=True)
    shipping_address = fields.String()
    notes = fields.String()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOutputSchema))

order_input_schema = OrderInputSchema()
order_output_schema = OrderOutputSchema()
orders_output_schema = OrderOutputSchema(many=True)
order_schema = OrderOutputSchema()
orders_schema = OrderOutputSchema(many=True)