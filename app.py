import os
import requests
import operator
import re
import nltk
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from stop_words import stops
from collections import Counter
from bs4 import BeautifulSoup
from rq import Queue
from rq.job import Job
from worker import conn


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

q = Queue(connection=conn) # this sets up a Redis connection and initialize a queue based on that connection

from models import Result

@app.route('/', methods=['GET', 'POST'])
def index():
  errors = []
  results = {}
  if request.method == "POST":
    # get the url that the user has entered
    try:
      url = request.form['url']
      r = requests.get(url)
    except:
      errors.append(
        "Unable to get URL. Please make sure it's valid and try again."
      )
      return render_template('index.html', errors=errors)
    if r:
      # text processing
      raw = BeautifulSoup(r.text, 'html.parser').get_text()
      nltk.data.path.append('./nltk_data/') # set the path
      tokens = nltk.word_tokenize(raw)
      text = nltk.Text(tokens)
      # remove punctuation, count raw words
      nonPunct = re.compile('.*[A-Za-z].*')
      raw_words = [w for w in text if nonPunct.match(w)]
      raw_words_count = Counter(raw_words)
      # stop words
      no_stop_words = [w for w in raw_words if w.lower() not in stops]
      no_stop_words_counts = Counter(no_stop_words)
      # display and save results
      results = sorted(
        no_stop_words_counts.items(),
        key=operator.itemgetter(1),
        reverse=True
      )[:10]
      try:
        result = Result(
          url=url,
          result_all=raw_words_count,
          result_no_stop_words=no_stop_words_counts
        )
        db.session.add(result)
        db.session.commit()
      except:
        errors.append("Unable to add item to database")

  return render_template('index.html', errors=errors, results=results)

if __name__ == '__main__':
  app.run()
