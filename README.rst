###########
StudyHelper
###########

StudyHelper is a quiz/exam engine written in Python3, it was proposed to help students in their goals but you can use it for any purpose.
StudyHelper is also based on the let´s quiz project (https://github.com/akashgiricse/lets-quiz)

************
Requirements
************
docker

**********************************
Run it on docker using the commad:
**********************************
- docker run -it --rm --name study-helper-container -p 8000:8000 -e STUDY_HELPER_INITIAL_DATA=1 -e STUDY_HELPER_ADMIN_USERNAME=administrator -e STUDY_HELPER_ADMIN_PASSWORD=administrator dionyself/study-helper:latest


Login to 127.0.0.1:8000/

user: administrator

password: administrator

*********
Features:
*********
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

************
Coming soon:
************
- Backend improvements
- UI impovements
- Randomizer improvements
- Exam/session results panel
- Printer friendly exams
- Invite non registered users to take exams


.. |bitcoin| image:: https://raw.githubusercontent.com/dionyself/golang-cms/master/static/img/btttcc.png
   :height: 230px
   :width: 230 px
   :alt: Donate with Bitcoin

.. |xmr| image:: https://raw.githubusercontent.com/dionyself/golang-cms/master/static/img/xmmr.jpeg
   :height: 250px
   :width: 250 px
   :alt: Donate with Monero
   
.. |paypal| image:: https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif
   :height: 100px
   :width: 200 px
   :alt: Donate with Paypal
   :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=L4H5TUWZTZERS

*********************
Contribute and donate
*********************

+------------------------------+
| Donate to this project       |
+-----------+-------+----------+
| Bitcoin   |  XMR  | Paypal   |
+-----------+-------+----------+
| |bitcoin| + |xmr| + |paypal| +
+-----------+-------+----------+

**********
DISCLAIMER
**********
This application/program is not ready for production,
therefore I do not offer any kind of warranties.

