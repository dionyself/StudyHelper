. ../venv3.11/bin/activate
cd studyhelper
python manage.py makemigrations quiz
python manage.py migrate 
python manage.py createsuperuser
python manage.py runserver