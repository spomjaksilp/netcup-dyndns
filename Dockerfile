FROM  python:3.7-alpine

COPY nc_api/ nc_api/
COPY dyndns.py /
COPY settings.json /
COPY hosts.json /
COPY Pipfile /
COPY Pipfile.lock /

RUN pip install pipenv
RUN pipenv install

CMD pipenv run dyndns settings.json hosts.json --ttl 300 --update
