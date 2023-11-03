del /S /Q main\migrations\*
del /S /Q db.sqlite3
python manage.py makemigrations main
python manage.py migrate
python manage.py loaddata init_data.json
python manage.py runserver