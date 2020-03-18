export FLASK_ENV=development
pytest -v test_newsapp.py

coverage run --source=news_app test_newsapp.py
coverage html