import requests
from bs4 import BeautifulSoup
from nltk.sentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from datetime import datetime
import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import nltk

nltk.download('vader_lexicon')


class NewsScraper:
    def __init__(self, websites):
        self.websites = websites

    def scrape_articles(self):
        news_articles = []

        for website in self.websites:
            response = requests.get(website)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')

            for article in articles:
                if article.find('h2', class_='title') is not None:
                    title = article.find('h2', class_='title').text.strip()
                else:
                    title = ""
                if article.find('span', class_='author') is not None:
                    author = article.find('span', class_='author').text.strip()
                else:
                    author = ""
                if article.find('p') is not None:
                    content = article.find('p').text.strip()
                else:
                    content = ""

                news_article = {
                    'publication_date': datetime.now().strftime("%Y-%m-%d"),
                    'title': title,
                    'author': author,
                    'content': content
                }
                news_articles.append(news_article)

        return news_articles


class NewsSummarizer:
    def __init__(self):
        self.summarizer = pipeline('summarization')

    def summarize(self, article):
        summary = self.summarizer(
            article['content'], max_length=120, min_length=30, do_sample=False)[0]['summary_text']

        article['summary'] = summary
        return article


class SentimentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()

    def analyze_sentiment(self, article):
        sentiment_scores = self.sia.polarity_scores(article['content'])

        article['sentiment'] = sentiment_scores
        return article


class ArticleCategorizer:
    def __init__(self):
        self.categories = {
            'climate_change': ['climate change'],
            'biodiversity': ['biodiversity'],
            'pollution': ['pollution'],
            'renewable_energy': ['renewable energy']
        }

    def categorize_articles(self, articles):
        categorized_articles = {category: [] for category in self.categories}

        for article in articles:
            categorized = False
            for category, keywords in self.categories.items():
                for keyword in keywords:
                    if keyword in article['content']:
                        categorized_articles[category].append(article)
                        categorized = True
                        break
                if categorized:
                    break

        return categorized_articles


class WordCloudGenerator:
    def generate_word_cloud(self, articles):
        text = ' '.join([article['content'] for article in articles])

        stopwords = set(STOPWORDS)

        wordcloud = WordCloud(width=800, height=400,
                              stopwords=stopwords).generate(text)

        plt.figure(figsize=(12, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.show()


class NewsUpdater:
    def __init__(self, scraper, summarizer, sentiment_analyzer, categorizer, wordcloud_generator):
        self.scraper = scraper
        self.summarizer = summarizer
        self.sentiment_analyzer = sentiment_analyzer
        self.categorizer = categorizer
        self.wordcloud_generator = wordcloud_generator

    def fetch_and_analyze_news(self):
        news_articles = self.scraper.scrape_articles()
        analyzed_articles = []

        for article in news_articles:
            summarized_article = self.summarizer.summarize(article)
            analyzed_article = self.sentiment_analyzer.analyze_sentiment(
                summarized_article)
            analyzed_articles.append(analyzed_article)

        categorized_articles = self.categorizer.categorize_articles(
            analyzed_articles)
        self.wordcloud_generator.generate_word_cloud(news_articles)
        return categorized_articles


class EmailSender:
    def send_email(self, subject, content, receiver_email, sender_email, sender_password):
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject

        message.attach(MIMEText(content))

        with smtplib.SMTP('smtp.gmail.com', 587) as session:
            session.starttls()
            session.login(sender_email, sender_password)

            text = message.as_string()
            session.sendmail(sender_email, receiver_email, text)


class NewsSubscription:
    def __init__(self, news_updater, email_sender, categories, receiver_email, sender_email, sender_password):
        self.news_updater = news_updater
        self.email_sender = email_sender
        self.categories = categories
        self.receiver_email = receiver_email
        self.sender_email = sender_email
        self.sender_password = sender_password

    def subscribe_to_news_categories(self):
        categorized_articles = self.news_updater.fetch_and_analyze_news()

        for category, articles in categorized_articles.items():
            if category in self.categories and len(articles) > 0:
                subject = f"Latest {category.replace('_', ' ').title()} News"
                content = '\n\n'.join(
                    [f"Title: {article['title']}\nSummary: {article['summary']}\n" for article in articles])
                self.email_sender.send_email(subject, content, self.receiver_email, self.sender_email,
                                             self.sender_password)


if __name__ == "__main__":
    websites = [
        "https://www.nationalgeographic.com/",
        "https://www.greenpeace.org/",
        "https://www.worldwildlife.org/"
    ]

    # Instantiate classes
    scraper = NewsScraper(websites)
    summarizer = NewsSummarizer()
    sentiment_analyzer = SentimentAnalyzer()
    categorizer = ArticleCategorizer()
    wordcloud_generator = WordCloudGenerator()
    email_sender = EmailSender()

    # Set up configurations
    receiver_email = "receiver_email@gmail.com"
    sender_email = "your_email@gmail.com"
    sender_password = "your_email_password"
    categories = ['climate_change', 'biodiversity',
                  'pollution', 'renewable_energy']

    # Create instances of NewsUpdater and NewsSubscription
    updater = NewsUpdater(scraper, summarizer,
                          sentiment_analyzer, categorizer, wordcloud_generator)
    subscription = NewsSubscription(
        updater, email_sender, categories, receiver_email, sender_email, sender_password)

    # Set up news subscription schedule
    schedule.every().day.at("09:00").do(subscription.subscribe_to_news_categories)

    # Continuously run the schedule
    while True:
        schedule.run_pending()
        time.sleep(1)
