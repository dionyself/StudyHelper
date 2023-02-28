FROM python:3.11.2-alpine3.17

ENV DJANGO_SETTINGS_MODULE studyhelper.settings

USER root

RUN apk add --no-cache git curl \
    && apk add --no-cache su-exec

ENV HOME  /root


RUN cd /root && git clone https://github.com/dionyself/StudyHelper.git && cd /root/StudyHelper/studyhelper && git checkout main
WORKDIR /root/StudyHelper/studyhelper
RUN cd /root/StudyHelper/studyhelper && pip install -r requirements.txt && pip freeze

COPY ./studyhelper/data/ /root/StudyHelper/studyhelper/data

USER root

EXPOSE 8000

# Start app
CMD ["/root/StudyHelper/studyhelper/start.sh"]
