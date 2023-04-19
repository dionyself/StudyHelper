#docker build -t dionyself/study-helper:latest .
#docker push dionyself/study-helper:latest
#docker run -it --rm --name study-helper-container -p 8000:8000 -e STUDY_HELPER_INITIAL_DATA=1 -e STUDY_HELPER_ADMIN_USERNAME=administrator -e STUDY_HELPER_ADMIN_PASSWORD=administrator dionyself/study-helper:latest
#docker stop study-helper-container
#docker start study-helper-container
#docker rm -v study-helper-container
#docker rmi dionyself/study-helper:latest

#docker run -it --rm --name study-helper-container -p 8000:8000 -e STUDY_HELPER_INITIAL_DATA=0 -e STUDY_HELPER_ADMIN_USERNAME=administrator -e STUDY_HELPER_ADMIN_PASSWORD=administrator dionyself/study-helper:latest
#docker exec -it study-helper-container sh -c "ls"
#docker run -it --rm -p 8000:8000 -e STUDY_HELPER_INITIAL_DATA=0 -e STUDY_HELPER_ADMIN_USERNAME=administrator -e STUDY_HELPER_ADMIN_PASSWORD=administrator --name study-helper-container dionyself/study-helper:latest


. ../venv3.11/bin/activate
cd studyhelper
python manage.py makemigrations quiz
python manage.py makemigrations invite
python manage.py migrate 
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.get(username='admin', is_superuser=True).delete()"
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('administrator', 'admin@localhost', 'administrator')"

python manage.py runserver