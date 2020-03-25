export FLASK_ENV=development
# regular python unittest
pytest -v test_newsapp.py

# statement coverage
coverage run --source=news_app test_newsapp.py
coverage html

# branch coverage
coverage run --branch --source=news_app test_newsapp.py
coverage html