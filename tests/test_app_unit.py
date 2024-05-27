"""Unit tests for app that are isolated from external systems."""

import os
from unittest.mock import MagicMock, patch

import plotly.graph_objects as go
import pytest
from conftest import EXAMPLE_EMAIL, EXAMPLE_PASSWORD

from src.markets import app


def test_main(mock_email_server, mock_secrests_manager_client, mock_df):
    try:
        app.main()
    except Exception as e:
        pytest.fail(f"main() raised exception: {e}")

    mock_email_server.login.assert_called_once_with(
        user=EXAMPLE_EMAIL, password=EXAMPLE_PASSWORD
    )
    mock_email_server.sendmail.assert_called_once()
    mock_secrests_manager_client.get_secret_value.assert_called_once_with(
        SecretId=app.SECRET_ID
    )


def test_setup_envs(mock_secrests_manager_client):
    app.setup_envs()
    assert os.environ["GMAIL_PASSWORD"] == EXAMPLE_PASSWORD
    assert os.environ["GMAIL_ADDRESS"] == EXAMPLE_EMAIL


def test_get_secrets(mock_secrests_manager_client):
    expected = {"GMAIL_ADDRESS": EXAMPLE_EMAIL, "GMAIL_PASSWORD": EXAMPLE_PASSWORD}
    result = app.get_secrets(secret_id=app.SECRET_ID)
    assert result == expected
    mock_secrests_manager_client.get_secret_value.assert_called_once_with(
        SecretId=app.SECRET_ID
    )


@patch("boto3.session.Session.client")
def test_get_secrets_invalid(mock_client):
    mock_client.get_secret_value.side_effect = Exception("Mock exception")
    result = app.get_secrets(secret_id=app.SECRET_ID)
    assert result is None


def test_send_email(mock_envs, mock_email_server):
    mock_message = MagicMock()
    app.send_email(mock_message)
    mock_email_server.login.assert_called_once_with(
        user=EXAMPLE_EMAIL, password=EXAMPLE_PASSWORD
    )
    mock_email_server.sendmail.assert_called_once()


def test_send_email_invalid(mock_email_server):
    mock_message = MagicMock()
    with pytest.raises(
        ValueError,
        match=(
            "GMAIL_ADDRESS and GMAIL_PASSWORD environment variables and needed to "
            "send email."
        ),
    ):
        app.send_email(mock_message)


def test_create_metrics(mock_df):
    result = app.create_metrics(mock_df)
    assert not result.empty
    columns = [
        "risk_cryptoverse",
        "risk_logpoly",
        "previous_high",
    ]
    assert all(column in result.columns for column in columns)
    assert len(result.columns) == len(set(result.columns))


def test_update_margin():
    fig = go.Figure()
    result = app.update_margin(fig)
    margins = result.layout.margin
    assert margins.l == 5
    assert margins.r == 5
    assert margins.t == 5
    assert margins.b == 5
