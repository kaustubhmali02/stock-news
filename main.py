import datetime
import requests
from twilio.rest import Client
import re
import os

CLEANER = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

STOCK_NAME = "TSLA"
COMPANY_NAME = "Tesla Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

ALPHA_ADVANTAGE_API_KEY = os.environ['ALPHA_ADVANTAGE_API_KEY']
NEWS_API_KEY = os.environ['NEWS_API_KEY']

TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
MY_TWILIO_NUMBER = os.environ['MY_TWILIO_NUMBER']
MY_PHONE = os.environ['MY_PHONE']

today = datetime.date.today()
yesterday = str(today - datetime.timedelta(days=1))
day_before_yesterday = str(today - datetime.timedelta(days=2))


def cleanhtml(raw_html):
    cleantext = re.sub(CLEANER, '', raw_html)
    return cleantext


def get_percentage_difference():
    parameters = {
        "function": "TIME_SERIES_DAILY",
        "symbol": STOCK_NAME,
        "apikey": ALPHA_ADVANTAGE_API_KEY
    }

    response = requests.get(url=STOCK_ENDPOINT, params=parameters)
    response.raise_for_status()
    stock_data = response.json()["Time Series (Daily)"]
    yesterday_stock_close_price = float(stock_data[yesterday]["4. close"])
    day_before_yesterday_stock_close_price = float(stock_data[day_before_yesterday]["4. close"])

    stock_closing_diff = abs(yesterday_stock_close_price - day_before_yesterday_stock_close_price)

    percentage_difference = float("{:.2f}".format(stock_closing_diff / ((yesterday_stock_close_price +
                                                                         day_before_yesterday_stock_close_price) / 2)
                                                  * 100))
    return percentage_difference


def get_news():
    news_parameters = {
        "apiKey": NEWS_API_KEY,
        "q": COMPANY_NAME,
        "searchIn": 'title,description',
        # "from": today,
        # "to": day_before_yesterday,
        # "language": "en"
    }

    news_response = requests.get(url=NEWS_ENDPOINT, params=news_parameters)
    news_response.raise_for_status()
    articles = news_response.json()["articles"][:3]
    article_headlines = [cleanhtml(article["title"]) for article in articles]
    article_descriptions = [cleanhtml(article["description"]) for article in articles]
    return article_headlines, article_descriptions


def send_msg(article_headline, article_description, percentage_difference):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    if percentage_difference > 5:
        body = f"{COMPANY_NAME}: 🔺{percentage_difference}\nHeadline: {article_headline}\nBrief: {article_description}"

    else:
        body = f"{COMPANY_NAME}: 🔻{percentage_difference}\nHeadline: {article_headline}\nBrief: {article_description}"

    message = client.messages.create(
        body=f"{body}",
        from_=MY_TWILIO_NUMBER,
        to=MY_PHONE
    )
    print(message.sid)


percentage_diff = get_percentage_difference()
if percentage_diff > 5:
    news = get_news()
    headlines = news[0]
    description = news[1]
    index = 0
    for _ in range(len(headlines)):
        send_msg(headlines[index], description[index], percentage_diff)
        index += 1
