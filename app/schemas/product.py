from marshmallow import Schema, fields, validate

class ProductSchema(Schema):
    id = fields.UUID(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(allow_none=True)
    sku = fields.String(required=True, validate=validate.Length(min=1, max=100))
    price = fields.Decimal(required=True, as_string=True)
    stock_quantity = fields.Integer(load_default=0)
    is_active = fields.Boolean(load_default=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

# Instantiate the schemas for single and multiple items
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)