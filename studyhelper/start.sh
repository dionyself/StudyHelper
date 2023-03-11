#!/bin/bash

export STUDY_HELPER_INITIAL_DATA=${STUDY_HELPER_INITIAL_DATA:="0"}
export STUDY_HELPER_ADMIN_USERNAME=${STUDY_HELPER_ADMIN_USERNAME:="administrator"}
export STUDY_HELPER_ADMIN_PASSWORD=${STUDY_HELPER_ADMIN_PASSWORD:="administrator"}
export STUDY_HELPER_ADMIN_EMAIL=${STUDY_HELPER_ADMIN_EMAIL:="adm@localhost"}

cd /root/StudyHelper/studyhelper
python manage.py makemigrations quiz
python manage.py migrate 
#python manage.py createsuperuser
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.get(username='admin', is_superuser=True).delete()"
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('$STUDY_HELPER_ADMIN_USERNAME', '$STUDY_HELPER_ADMIN_EMAIL', '$STUDY_HELPER_ADMIN_PASSWORD')"
if [ $STUDY_HELPER_INITIAL_DATA -eq "1" ]; then
    python manage.py shell -c "from quiz.views import import_json_course; import_json_course([open('/root/StudyHelper/studyhelper/data/initial.json', 'r')])"
fi
python manage.py runserver 0.0.0.0:8000
