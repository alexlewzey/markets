"""Integration tests for app that interact with external systems."""
from datetime import date

import pandas as pd
import pytest
from conftest import _test_aws_credentials

from src.markets.app import download_btc


def test_download_btc():
    try:
        df = download_btc()
    except Exception as e:
        pytest.fail(f"download_btc exception: {e}")
    assert isinstance(df, pd.DataFrame)
    expected_columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    assert df.columns.tolist() == expected_columns
    expected_schema = {
        "Date": "object",
        "Open": "float64",
        "High": "float64",
        "Low": "float64",
        "Close": "float64",
        "Adj Close": "float64",
        "Volume": "int64",
    }
    for column, dtype in expected_schema.items():
        assert df[column].dtype == dtype
    assert not df.empty, "df is empty"
    for column in expected_columns[1:]:
        assert (df[column] >= 0).all(), "Negative values detected"

    assert (df.isnull().mean() == 0).all(), "Null values detected"

    try:
        df["Date"].apply(date.fromisoformat)
    except ValueError as e:
        pytest.fail(f"Invalid dates detected: {e}")


def test_aws_credentials():
    _test_aws_credentials()


def test_send_email():
    # would require setting up a staging email account
    pass
