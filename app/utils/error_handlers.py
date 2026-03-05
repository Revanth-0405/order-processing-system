import logging
from flask import jsonify
from marshmallow import ValidationError

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err):
        app.logger.warning(f"Validation error: {err.messages}")
        return jsonify({"errors": err.messages}), 400

    @app.errorhandler(ValueError)
    def handle_value_error(err):
        app.logger.warning(f"Business logic error: {str(err)}")
        return jsonify({"message": str(err)}), 400

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"message": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(err):
        app.logger.error(f"Internal server error: {str(err)}")
        return jsonify({"message": "An internal server error occurred"}), 500