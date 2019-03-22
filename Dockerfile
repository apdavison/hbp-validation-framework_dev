#
# Build an image for deploying the Brain Simulation Platform Validation Service
#
# To build the image, from this directory:
#   docker build -t hbp_validation_service .
#
# To run the application:
#   docker run -d -p 443 -v /etc/letsencrypt:/etc/letsencrypt hbp_validation_service

FROM debian:stretch-slim

MAINTAINER Andrew Davison <andrew.davison@unic.cnrs-gif.fr>

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update --fix-missing; apt-get -y -q install python3-dev python3-pip sqlite3 python3-psycopg2 supervisor build-essential nginx-extras git
RUN unset DEBIAN_FRONTEND

RUN pip3 install --upgrade pip
RUN pip3 install uwsgi

RUN echo "" >> /var/log/django.log

ENV SITEDIR /home/docker/site

RUN git clone https://github.com/HumanBrainProject/pyxus.git pyxus_src
RUN pip3 install -r pyxus_src/pyxus/requirements.txt; pip3 install pyxus_src/pyxus
RUN git clone https://github.com/apdavison/neural-activity-resource.git; cd neural-activity-resource; git checkout validation
RUN pip3 install neural-activity-resource/client

COPY packages /home/docker/packages
COPY validation_service $SITEDIR
COPY model_validation_api /home/docker/model_validation_api
# COPY build_info.json $SITEDIR

WORKDIR /home/docker

RUN pip3 install -r $SITEDIR/requirements.txt
ENV PYTHONPATH  /home/docker:/home/docker/site:/usr/local/lib/python3.5/dist-packages:/usr/lib/python3.5/dist-packages

WORKDIR $SITEDIR
RUN if [ -f $SITEDIR/db.sqlite3 ]; then rm $SITEDIR/db.sqlite3; fi
RUN python3 manage.py check
RUN python3 manage.py collectstatic --noinput --verbosity 0
#RUN cd $SITEDIR/static; tar xf static.tar

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s $SITEDIR/deployment/nginx-app.conf /etc/nginx/sites-enabled/
RUN ln -s $SITEDIR/deployment/supervisor-app.conf /etc/supervisor/conf.d/
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log

EXPOSE 443
# EXPOSE 8000

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisor-app.conf"]
