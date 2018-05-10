FROM ubuntu:16.04

RUN apt-get update
# Install Python
RUN apt-get install -y python

# Install pip
RUN apt-get install -y python-pip python-dev build-essential
RUN pip install --upgrade pip
RUN pip install --upgrade virtualenv


# Install app dependencies
RUN pip install pyzmq
RUN apt-get install -y nano git
RUN pip install simplejson

COPY ./Worker.py /home

CMD python3 /home/Worker.py

EXPOSE 2341