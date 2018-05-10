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

COPY ./SourceData.txt /home
COPY ./DataSource.py /home

EXPOSE 2341