import os
import gzip
import base64
import json
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def process_event(event: dict) -> dict:
    """Decode and decompress the AWS logs event."""
    try:
        decoded_payload = base64.b64decode(event.get("awslogs", {}).get("data"))
        uncompressed_payload = gzip.decompress(decoded_payload)
        payload = json.loads(uncompressed_payload)
        return payload
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise e

def process_error_payload(payload: dict) -> tuple:
    """Extract necessary information from the payload."""
    try:
        logGroup = payload.get("logGroup")
        logStream = payload.get("logStream")
        logEvents = payload.get("logEvents")
        lambda_function_name = payload.get("logGroup", "").split("/")[-1]
        error_msg = "\t".join(levent.get("message", "") for levent in logEvents)
        return logGroup, logStream, lambda_function_name, error_msg
    except Exception as e:
        logger.error(f"Error extracting error payload: {e}")
        raise e

def return_func(status_code=200, message="Success!", headers=None, isBase64Encoded=False) -> dict:
    """Helper function for returning an HTTP response."""
    if headers is None:
        headers = {"Content-Type": "application/json"}
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps({"message": message}),
        "isBase64Encoded": isBase64Encoded,
    }

def send_email(logGroup: str, logStream: str, lambda_function_name: str, error_msg: str) -> str:
    """Send an email notification via SNS."""
    sns_client = boto3.client("sns")
    SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
    
    if not SNS_TOPIC_ARN:
        logger.error("SNS_TOPIC_ARN is missing from environment variables!")
        return return_func(status_code=500, message="SNS topic ARN missing!")

    email_body = f"""
                        ================================================
                        Lambda Function Error Details
                        -----------------------------------------------
                        Lambda Function Name: {lambda_function_name}
                        Log Group: {logGroup}
                        Log Stream: {logStream}
                        Error Message: {error_msg}
                        ================================================
                        """

    email_subject = f"Error in Lambda Function: {lambda_function_name}"

    try:
        sns_client.publish(
            TargetArn=SNS_TOPIC_ARN,
            Subject=email_subject,
            Message=email_body
        )
        
        logger.info("Error email notification sent successfully!")
    except ClientError as e:
        logger.error(f"Failed to send SNS notification: {e}")
        return return_func(status_code=500, message="Failed to send notification!")

def lambda_handler(event, context):
    try:
        # Process the log event and extract error details
        payload = process_event(event)
        logGroup, logStream, lambda_function_name, error_msg = process_error_payload(payload)
        
        # Send the notification email
        send_email(logGroup, logStream, lambda_function_name, error_msg)
        
        # Return a success response
        return return_func(status_code=200, message="Error processed and email sent.")
    
    except Exception as e:
        logger.error(f"Unhandled error in Lambda: {e}")
        return return_func(status_code=500, message="Error processing the event.")
