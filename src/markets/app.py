import json
import os
import smtplib
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import boto3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

pio.kaleido.scope.chromium_args += (
    "--single-process",
)  # required for lambda environment

dir_tmp = Path("/tmp")  # only lambda directory with write permissions
dir_tmp.mkdir(exist_ok=True)

plot_kwargs = {"width": 1200, "height": 300}

SECRET_ID = "gmail"  # noqa: S105


def normalise(ser: pd.Series) -> pd.Series:
    return (ser - ser.min()) / (ser.max() - ser.min())


def update_margin(fig: go.Figure) -> go.Figure:
    fig.update_layout(margin={"l": 5, "r": 5, "t": 5, "b": 5})
    return fig


def download_btc() -> pd.DataFrame:
    print("Downloading btc")
    now = int(datetime.now().timestamp())
    start = int(now - (60 * 60 * 24 * 365 * 15))
    url = f"https://query1.finance.yahoo.com/v7/finance/download/BTC-USD?period1={start}&period2={now}&interval=1d&events=history&includeAdjustedClose=true"
    df = pd.read_csv(url)
    return df


def create_metrics(df: pd.DataFrame) -> pd.DataFrame:
    print("Creating metrics")
    df.columns = df.columns.str.lower()
    df["log_close"] = np.log(df["close"])
    df["iddf"] = range(df.shape[0])
    df["sma_50d"] = df.close.rolling(50).mean()
    df["sma_50w"] = df.close.rolling(50 * 7).mean()
    degree = 2
    poly = PolynomialFeatures(degree=degree)
    df_poly = poly.fit_transform(df[["iddf"]])
    for i in range(df_poly.shape[1]):
        df[f"p{i}"] = df_poly[:, i]
    columns = ["p0", "p1", "p2"]

    model = LinearRegression()
    model.fit(df[columns], df["log_close"])
    df["poly"] = model.predict(df[columns])

    years = range(2021, 2022)
    for y in years:
        model = LinearRegression()
        df_filt = df[df.date <= f"{y}-01-01"]
        model.fit(df_filt[columns], df_filt["log_close"])
        df[f"poly_{y}"] = model.predict(df[columns])

    df["risk_cryptoverse"] = normalise(
        np.log(df["sma_50d"] / df["sma_50w"] * df["poly"])
    )
    df["risk_diff"] = normalise(df["log_close"] - df["poly"])
    df["risk_logpoly"] = (
        normalise(np.log(df["risk_diff"] + 1) * df["poly"]).rolling(10).mean()
    )
    df["previous_high"] = df["close"].max()
    return df


def create_figures(metrics: pd.DataFrame) -> list[tuple]:
    print("Creating figures")
    figures = []
    melt = metrics.melt("date", ["risk_cryptoverse", "risk_logpoly"])
    fig = px.line(melt, "date", "value", color="variable", **plot_kwargs)
    for i in [0.4, 0.6, 0.2, 0.9]:
        fig.add_hline(i, line_dash="dash", line_color="black")
    fig = update_margin(fig)
    figures.append(
        (
            "risk_metrics",
            fig,
            "Timeseries of risk metrics with the buy/sell ranges overlayed",
        )
    )

    melt = metrics.melt(
        "date", ["close"] + metrics.filter(regex="^sma").columns.tolist()
    )
    fig = px.line(melt, "date", "value", color="variable", **plot_kwargs)
    fig = update_margin(fig)
    figures.append(
        (
            "price_ts",
            fig,
            "Timeseries of close price, 50 day and 50 week moving averages",
        )
    )

    metrics["poly_upper"] = metrics["poly"] + 1.5
    metrics["poly_lower"] = metrics["poly"] - 1
    melt = metrics.melt("date", ["log_close", "poly", "poly_upper", "poly_lower"])
    fig = px.line(melt, "date", "value", color="variable", **plot_kwargs)
    fig = update_margin(fig)
    figures.append(
        ("polynomial_fit", fig, "Timeseries of log close price with polynomial fit")
    )

    fig = px.scatter(metrics, "date", "close", color="risk_logpoly", **plot_kwargs)
    fig = update_margin(fig)
    figures.append(
        ("colored_ts", fig, "Timeseries of close price colored by risk metric")
    )
    return figures


def create_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    print("Creating summary table")
    display_columns = ["close", "previous_high", "risk_cryptoverse", "risk_logpoly"]
    indexes = (-np.array([1, 2, 3, 7, 30, 90, 180, 360])).tolist()
    table = df[display_columns].iloc[indexes]
    table["lag_days"] = indexes
    for c in ["close", "previous_high"]:
        table[c] = table[c].apply(lambda x: f"{x:,.0f}")
    for c in ["risk_cryptoverse", "risk_logpoly"]:
        table[c] = table[c].apply(lambda x: f"{x:.2f}")
    table = table.set_index("lag_days")
    return table


def create_message(figures: list[tuple], table: pd.DataFrame) -> MIMEMultipart:
    print("Creating message")
    email_address = os.getenv("GMAIL_ADDRESS")
    message = MIMEMultipart("related")
    message["Subject"] = "Market report"
    message["From"] = email_address
    message["To"] = email_address

    figures_html = ""
    for name, _, desc in figures:
        figures_html += f"""<p>{desc}</p>\n<img src="cid:{name}">\n"""

    html = f"""\
    <html>
    <head></head>
    <body>
        {table.to_html()}
        {figures_html}
    </body>
    </html>
    """
    body = MIMEText(html, "html")
    message.attach(body)

    for name, fig, _ in figures:
        path = dir_tmp / f"{name}.png"
        fig.write_image(path)
        with path.open("rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", f"<{name}>")
            message.attach(img)
    return message


def send_email(message: MIMEMultipart) -> None:
    print("Sending email")
    email_address = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_PASSWORD")
    if (email_address is None) or (password is None):
        raise ValueError(
            "GMAIL_ADDRESS and GMAIL_PASSWORD environment variables "
            "and needed to send email."
        )
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(user=email_address, password=password)
            server.sendmail(email_address, email_address, message.as_string())
        print("Successfully sent email")
    except Exception as e:
        print(f"Failed to send email: {e}")


def get_secrets(secret_id: str) -> dict | None:
    print("Getting secrests")
    try:
        session = boto3.session.Session()
        client = session.client(service_name="secretsmanager")
        result = client.get_secret_value(SecretId=secret_id)
        secrets = json.loads(result["SecretString"])
        return secrets
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            print(f"Secret `{secret_id}` not found: {error_code}")
        else:
            print(f"ClientError getting secret `{secret_id}`: {error_code}")
        return None
    except Exception:
        print(f"Exception getting secret `{secret_id}`")
        return None


def setup_envs() -> None:
    secrets = get_secrets(secret_id=SECRET_ID)
    if secrets:
        print("Reading secrets from aws secrets manager")
        for k, v in secrets.items():
            os.environ[k] = v
    else:
        print("Reading secrets from local .env")
        load_dotenv()


def main() -> None:
    setup_envs()
    df = download_btc()
    metrics = create_metrics(df)
    table = create_summary_table(metrics)
    figures = create_figures(metrics)
    message = create_message(figures, table)
    send_email(message)


def handler(event, context):
    try:
        main()
        return {"statusCode": 200, "body": "Email sent successfully!"}
    except Exception as e:
        return {
            "statusCode": 400,
            "body": f"Error: {e}",
        }


if __name__ == "__main__":
    main()
