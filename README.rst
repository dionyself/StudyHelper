# StudyHelper
StudyHelper is a quiz/exam engine written in Python3, it was proposed to help students in their goals but you can use it for any purpose.
StudyHelper is also based on the let´s quiz project (https://github.com/akashgiricse/lets-quiz)


## Requirements
docker

## Run it on docker using the commad:
docker run -it --rm --name study-helper-container -p 8000:8000 -e STUDY_HELPER_INITIAL_DATA=1 -e STUDY_HELPER_ADMIN_USERNAME=administrator -e STUDY_HELPER_ADMIN_PASSWORD=administrator dionyself/study-helper:latest


## Visit to login
127.0.0.1:8000/
user: administrator
password: administrator

## Features:
- Course and tags support
- Create course and topic specific exams
- Multiple choice question support
- Multiple correct choices support
- Exam scheduler
- Free question mode
- Leaderboar panel with the top users
- Question and Choice randomizer
- Explanation/reason support, explaining why a choice is wrong/right
- Supports expertise levels on questions, courses and exams
- Export/import questions
- AI promnt avaliable, so you can use AI to generate importable exams

## Coming soon:
- Backend improvements
- UI impovements
- Randomizer improvements
- Exam/session results panel
- Printer friendly exams
- Invite non registered users to take exams


### DISCLAIMER
This application/program is not ready for production,
therefore I do not offer any kind of warranties.
