from flask import (Flask, render_template, request)
import sqlite3
from flask import g
import geopy.distance
import openai

DATABASE = 'db/shield.db'
openai.api_key = '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'

app = Flask(__name__)


def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
  db.row_factory = sqlite3.Row
  return db


@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()


def query_db(query, args=(), one=False):
  cur = get_db().execute(query, args)
  rv = cur.fetchall()
  cur.close()
  return (rv[0] if rv else None) if one else rv


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/result')
def result():
  code = request.args.get('code')
  miles = request.args.get('miles')

  description_en = query_db(
    f'select * from proceduremetadata where code={code}')[0]['description_en']

  data = []
  for table in query_db(
      f'select * from procedure as p join hospital as h ON p.hospital_id = h.id where code={code} order by cash_charge ASC'
  ):
    latitude = table['latitude']
    longitude = table['longitude']
    distance = geopy.distance.distance((latitude, longitude),
                                       (30.2672, -97.7431)).miles
    if distance < float(miles):
      data.append({
        'cash_charge': '${:,.2f}'.format(table['cash_charge']),
        'gross_charge': '${:,.2f}'.format(table['gross_charge']),
        'percent_off': '{:,.2f}%'.format((1 - (table['cash_charge']/table['gross_charge']))*100),
        'name': table['name']
      })
  return render_template(
    'result.html',
    data=data,
    code=code,
    procedure_url=f'https://www.aapc.com/codes/cpt-codes/{code}',
    description_en=description_en)


app.run(host='0.0.0.0', port=81)
