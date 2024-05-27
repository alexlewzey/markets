"""Post deployment tests."""
import boto3
import pytest
from conftest import _test_aws_credentials

REPOSITORY_NAME: str = "market-lambda-repository"
FUNCITON_NAME: str = "market-lambda"
SCHEDULE_NAME: str = "daily-lambda-trigger"


def test_aws_credentials():
    _test_aws_credentials()


def test_ecr_repository_exists():
    ecr_client = boto3.client("ecr")
    try:
        response = ecr_client.describe_repositories(repositoryNames=[REPOSITORY_NAME])
        assert response["repositories"][0]["repositoryName"] == REPOSITORY_NAME
    except ecr_client.exceptions.ResourceNotFoundException as e:
        pytest.fail(f"ECR repository does not exist: {e}")
    except Exception as e:
        pytest.fail(f"ECR repository exception: {e}")


def test_lambda_function_exists():
    lambda_client = boto3.client("lambda")
    try:
        res = lambda_client.get_function(FunctionName=FUNCITON_NAME)
        assert res["Configuration"]["FunctionName"] == FUNCITON_NAME
    except lambda_client.exceptions.ResourceNotFoundException as e:
        pytest.fail(f"lambda function does not exist: {e}")
    except Exception as e:
        pytest.fail(f"lambda function exception: {e}")


def test_schedule_exists():
    scheduler_client = boto3.client("scheduler")
    try:
        res = scheduler_client.get_schedule(Name=SCHEDULE_NAME)
        assert res["Name"] == SCHEDULE_NAME
    except scheduler_client.exceptions.ResourceNotFoundException as e:
        pytest.fail(f"schedule does not exist: {e}")
    except Exception as e:
        pytest.fail(f"schedule exception: {e}")


def test_lambda_permission_exists():
    try:
        lambda_client = boto3.client("lambda")
        policy = lambda_client.get_policy(FunctionName=FUNCITON_NAME)["Policy"]
        assert "scheduler.amazonaws.com" in policy
    except lambda_client.exceptions.ResourceNotFoundException:
        pytest.fail(
            "Lambda function does not have correct permissions for EventBridge schedule"
        )
    except Exception as e:
        pytest.fail(f"lambda permission exception: {e}")