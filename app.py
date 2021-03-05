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

def count_and_save_words(url):
  errors = []

  try:
      r = requests.get(url)
  except:
      errors.append(
        "Unable to get URL. Please make sure it's valid and try again."
      )
      return {"error": errors}

  # text processing
  raw = BeautifulSoup(r.text).get_text()
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

  # save results
  try:
    result = Result(
      url=url,
      result_all=raw_words_count,
      result_no_stop_words=no_stop_words_counts
    )
    db.session.add(result)
    db.session.commit()
    return result.id
  except:
    errors.append("Unable to add item to database")
    return {"error": errors}

@app.route('/', methods=['GET', 'POST'])
def index():
  results = {}
  if request.method == "POST":
    # this import solves a rq bug which currently exists
    from app import count_and_save_words

    # get url that the person has entered
    url = request.form['url']
    if not url[:8].startwith(('https://', 'http://')):
      url = 'http://' + url
    job = q.enqueue_call(
      func=count_and_save_words, args=(url,), result_ttl=5000
    )
    print(job.get_id)

    return render_template('index.html', results=results)

@app.route("/results/<job_key", methods=['GET'])
def get_results(job_key):

  job = Job.fetch(job_key, connection=conn)
  if job.is_finished:
    return str(job.result), 200
  else:
    return "Nay!", 202

if __name__ == '__main__':
  app.run()
