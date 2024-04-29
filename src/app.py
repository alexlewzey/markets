import os
import smtplib
from datetime import date, datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

from core import dir_data, dir_tmp

kwargs = {"width": 1200, "height": 300}


def normalise(ser: pd.Series) -> pd.Series:
    return (ser - ser.min()) / (ser.max() - ser.min())


def update_margin(fig: go.Figure) -> go.Figure:
    fig.update_layout(margin=dict(l=5, r=5, t=5, b=5))
    return fig


def create_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    display_columns = ["close", "previous_high", "risk_cryptoverse", "risk_logpoly"]
    indexes = (-np.array([1, 7, 30, 90, 180, 360])).tolist()
    table = df[display_columns].iloc[indexes]
    table["lag_days"] = indexes
    for c in ["close", "previous_high"]:
        table[c] = table[c].apply(lambda x: f"{x:,.0f}")
    for c in ["risk_cryptoverse", "risk_logpoly"]:
        table[c] = table[c].apply(lambda x: f"{x:.2f}")
    table = table.set_index("lag_days")
    return table


def create_metrics(write_csv: bool = False) -> pd.DataFrame:
    now = int(datetime.now().timestamp())
    start = int(now - (60 * 60 * 24 * 365 * 15))
    url = f"https://query1.finance.yahoo.com/v7/finance/download/BTC-USD?period1={start}&period2={now}&interval=1d&events=history&includeAdjustedClose=true"
    df = pd.read_csv(url)
    if write_csv:
        df.to_csv(dir_data / f"BTC-USD_{date.today()}.csv", index=False)
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
    df["poly"] = model.predict(df_poly)

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


def create_figures(df: pd.DataFrame) -> list[tuple]:
    figures = []
    melt = df.melt("date", ["risk_cryptoverse", "risk_logpoly"])
    fig = px.line(melt, "date", "value", color="variable", **kwargs)
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

    melt = df.melt("date", ["close"] + df.filter(regex="^sma").columns.tolist())
    fig = px.line(melt, "date", "value", color="variable", **kwargs)
    fig = update_margin(fig)
    figures.append(
        (
            "price_ts",
            fig,
            "Timeseries of close price, 50 day and 50 week moving averages",
        )
    )

    df["poly_upper"] = df["poly"] + 1.5
    df["poly_lower"] = df["poly"] - 1
    melt = df.melt("date", ["log_close", "poly", "poly_upper", "poly_lower"])
    fig = px.line(melt, "date", "value", color="variable", **kwargs)
    fig = update_margin(fig)
    figures.append(
        ("polynomial_fit", fig, "Timeseries of log close price with polynomial fit")
    )

    fig = px.scatter(df, "date", "close", color="risk_logpoly", **kwargs)
    fig = update_margin(fig)
    figures.append(
        ("colored_ts", fig, "Timeseries of close price colored by risk metric")
    )
    return figures


def create_message(figures: list[tuple], table: pd.DataFrame) -> MIMEMultipart:
    email_address = os.getenv("GMAIL")
    message = MIMEMultipart("related")
    message["Subject"] = "Market report"
    message["From"] = email_address
    message["To"] = email_address

    figures_html = ""
    for name, fig, desc in figures:
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

    for name, fig, desc in figures:
        path = dir_tmp / f"{name}.png"
        fig.write_image(path)
        with path.open("rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", f"<{name}>")
            message.attach(img)
    return message


def send_email(message: MIMEMultipart) -> None:
    email_address = os.getenv("GMAIL")
    password = os.getenv("PASSWORD")
    if (email_address is None) or (password is None):
        raise ValueError(
            "GMAIL and PASSWORD environment variables and needed to send email."
        )
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(email_address, password)
        server.sendmail(email_address, email_address, message.as_string())
        server.quit()
        print("Successfully sent email")
    except Exception as e:
        print(f"Failed to send email: {e}")


def main() -> None:
    load_dotenv()
    df = create_metrics()
    table = create_summary_table(df)
    figures = create_figures(df)
    message = create_message(figures, table)
    send_email(message)


if __name__ == "__main__":
    main()
