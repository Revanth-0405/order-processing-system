import os
from dotenv import load_dotenv

# Load environment variables from the .env file FIRST
load_dotenv()

from app import create_app

# Default to 'dev' if FLASK_ENV is not set
config_name = os.getenv('FLASK_ENV', 'dev')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)