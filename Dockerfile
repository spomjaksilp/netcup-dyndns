# tiny alpine python image
FROM  python:3.8-alpine

# install pipenv
RUN pip install pipenv

# set the working directory to /app
RUN mkdir app

# add app user
RUN adduser -D -u 1000 appuser

# grant access to app/
RUN chown  -R appuser app/

# be appuser
USER appuser

# copy the current directory contents into the container at /app
ADD . /app

# change working dir
WORKDIR /app

# python stuff
RUN pipenv install

CMD pipenv run dyndns settings.json hosts.json --ttl 300 --update
