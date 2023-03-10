. ../venv3.11/bin/activate
cd studyhelper
python manage.py makemigrations quiz
python manage.py migrate 
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.get(username='admin', is_superuser=True).delete()"
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('dionyself', 'test@localhost', 'system64')"
python manage.py runserver