import argparse
import json

import boto3
from botocore.exceptions import ClientError


def create_secret(
    gmail_address,
    gmail_password,
    aws_access_key_id,
    aws_secret_access_key,
    region_name="us-west-2",
):
    client = boto3.client(
        "secretsmanager",
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )

    secret_value = {"GMAIL_ADDRESS": gmail_address, "GMAIL_PASSWORD": gmail_password}

    try:
        response = client.create_secret(
            Name="gmail", SecretString=json.dumps(secret_value)
        )
        return response
    except ClientError as e:
        print(f"An error occurred: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Create an AWS Secrets Manager secret for Gmail credentials."
    )
    parser.add_argument("gmail_address", help="The Gmail address")
    parser.add_argument("gmail_password", help="The Gmail password")
    parser.add_argument("aws_access_key_id", help="The AWS access key ID")
    parser.add_argument("aws_secret_access_key", help="The AWS secret access key")

    args = parser.parse_args()

    response = create_secret(
        args.gmail_address,
        args.gmail_password,
        args.aws_access_key_id,
        args.aws_secret_access_key,
        region_name="eu-west-2",
    )
    if response:
        print("Secret created successfully")
        print(response)
    else:
        print("Failed to create secret")


if __name__ == "__main__":
    main()
