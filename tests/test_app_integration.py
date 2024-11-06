"""Integration tests for app that interact with external systems."""

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
    expected_columns = ["date", "close"]
    assert df.columns.tolist() == expected_columns
    expected_schema = {
        "date": "datetime64[ns, UTC]",
        "close": "float64",
    }
    for column, dtype in expected_schema.items():
        assert df[column].dtype == dtype
    assert not df.empty, "df is empty"
    for column in expected_columns[1:]:
        assert (df[column] >= 0).all(), "Negative values detected"

    assert (df.isnull().mean() == 0).all(), "Null values detected"


def test_aws_credentials():
    _test_aws_credentials()


def test_send_email():
    # would require setting up a staging email account
    pass
