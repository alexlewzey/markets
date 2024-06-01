import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import boto3
import pandas as pd
import pytest
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

EXAMPLE_EMAIL = "example@gmail.com"
EXAMPLE_PASSWORD = "example_password"  # noqa: S105


@pytest.fixture
def mock_email_server():
    print("Mocking email server")
    with patch("src.markets.app.smtplib.SMTP_SSL") as mock_smtp_ssl:
        email_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = email_server
        yield email_server


@pytest.fixture
def mock_secrests_manager_client():
    print("Mocking secrest manager client")
    with patch("src.markets.app.boto3.session.Session") as mock_session:
        secrests_manager_client = MagicMock()
        mock_session.return_value.client.return_value = secrests_manager_client
        mock_response = {
            "SecretString": json.dumps(
                {"GMAIL_ADDRESS": EXAMPLE_EMAIL, "GMAIL_PASSWORD": EXAMPLE_PASSWORD}
            )
        }
        secrests_manager_client.get_secret_value.return_value = mock_response
        yield secrests_manager_client
    os.environ.pop("GMAIL_PASSWORD", None)
    os.environ.pop("GMAIL_ADDRESS", None)


@pytest.fixture
def mock_envs():
    os.environ["GMAIL_PASSWORD"] = EXAMPLE_PASSWORD
    os.environ["GMAIL_ADDRESS"] = EXAMPLE_EMAIL
    yield
    os.environ.pop("GMAIL_PASSWORD")
    os.environ.pop("GMAIL_ADDRESS")


@pytest.fixture
def mock_df():
    print("Mocking df")
    path = Path(__file__).parent.parent / "data" / "BTC-USD_2024-05-26.csv"
    mock_df = pd.read_csv(path)
    with patch("src.markets.app.download_btc") as mock_download_btc:
        mock_download_btc.return_value = mock_df
        yield mock_df


def _test_aws_credentials():
    try:
        boto3.client("lambda").list_functions()
    except NoCredentialsError as e:
        pytest.fail(f"AWS credentials missing: {e}")
    except PartialCredentialsError as e:
        pytest.fail(f"AWS credentials partially missing: {e}")
    except Exception as e:
        pytest.fail(f"AWS credentials exception: {e}")
