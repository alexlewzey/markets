"""CLI tool to create the AWS secrets that are required for the app to run."""
import argparse
import json
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_secret(
    gmail_address: str,
    gmail_password: str,
    aws_access_key_id: str,
    aws_secret_access_key: str,
    region_name: str | None = None,
) -> dict | None:
    client = boto3.client(
        "secretsmanager",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )

    secret_value = {"GMAIL_ADDRESS": gmail_address, "GMAIL_PASSWORD": gmail_password}

    try:
        response = client.create_secret(
            Name="gmail", SecretString=json.dumps(secret_value)
        )
        return response
    except ClientError as e:
        logger.info(f"An error occurred: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an AWS Secrets Manager secret for Gmail credentials."
    )
    parser.add_argument("gmail_address", help="The Gmail address")
    parser.add_argument("gmail_password", help="The Gmail password")
    parser.add_argument("aws_access_key_id", help="The AWS access key ID")
    parser.add_argument("aws_secret_access_key", help="The AWS secret access key")
    parser.add_argument("region_name", help="The AWS region")

    args = parser.parse_args()

    response = create_secret(
        gmail_address=args.gmail_address,
        gmail_password=args.gmail_password,
        aws_access_key_id=args.aws_access_key_id,
        aws_secret_access_key=args.aws_secret_access_key,
        region_name=args.region_name,
    )
    if response:
        logger.info("Secret created successfully")
        logger.info(response)
    else:
        logger.info("Failed to create secret")


if __name__ == "__main__":
    main()
