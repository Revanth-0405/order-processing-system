import os
import json
import boto3
import logging
from importlib import import_module

logger = logging.getLogger(__name__)

class LambdaInvoker:
    @staticmethod
    def invoke(function_name, payload):
        """
        Invokes a Lambda function based on LAMBDA_MODE (local or aws).
        """
        mode = os.environ.get('LAMBDA_MODE', 'local')

        if mode == 'local':
            logger.info(f"Invoking local lambda: {function_name}")
            # Dynamically import the handler module from the lambdas directory
            module_name = f"lambdas.{function_name}.handler"
            try:
                module = import_module(module_name)
                # Mock a basic AWS Lambda context object
                context = {}
                # Call the handler function directly
                result = module.handler(payload, context)
                return result
            except Exception as e:
                logger.error(f"Error invoking local lambda {function_name}: {e}")
                raise e
        else:
            logger.info(f"Invoking AWS lambda: {function_name}")
            # Use boto3 to invoke the Lambda on AWS or LocalStack
            client = boto3.client(
                'lambda',
                endpoint_url=os.environ.get('AWS_ENDPOINT_URL'), # Useful for LocalStack
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
            
            response = client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse', # Synchronous invocation to get the result
                Payload=json.dumps(payload)
            )
            
            # Read and return the JSON response from the Lambda
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            return response_payload