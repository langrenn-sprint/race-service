# race-service
The race service let you administrate the main domain objects race and race plan.

Based on the type of event (competition format), list of race classes and a list of contestants, this service will support:

- generating a race plan, and
- generating races pr race classes with contestants and start times for each individual race.

The race service will support the following competition formats:

- Interval start competition,
- Mass start competition,
- Skiathlon competition,
- Pursuit,
- Individual sprint competition,
- Team sprint competition, and
- Relay competitions.

cf https://assets.fis-ski.com/image/upload/v1624284540/fis-prod/assets/ICR_CrossCountry_2022_clean.pdf

## Example of usage
```
% curl -H "Content-Type: application/json" \
  -X POST \
  --data '{"username":"admin","password":"passw123"}' \
  http://localhost:8081/login
% export ACCESS="" #token from response
% curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -X POST \
  --data @tests/files/event.json \
  http://localhost:8080/raceplans/generate-plan-for-event
% curl -H "Authorization: Bearer $ACCESS"  http://localhost:8080/raceplans
```

## Develop and run locally
### Requirements
- [pyenv](https://github.com/pyenv/pyenv) (recommended)
- [poetry](https://python-poetry.org/)
- [nox](https://nox.thea.codes/en/stable/)

```
% pipx install nox
% pipx install poetry
% pipx inject nox nox-poetry
```

### Install software:
```
% git clone https://github.com/Informasjonsforvaltning/dataservice-publisher.git
% cd dataservice-publisher
% pyenv install 3.9.6
% pyenv local 3.9.6
% poetry install
```
### Environment variables
To run the service locally, you need to supply a set of environment variables. A simple way to solve this is to supply a .env file in the root directory.

A minimal .env:
```
JWT_SECRET=secret
JWT_EXP_DELTA_SECONDS=3600
ADMIN_USERNAME=admin
ADMIN_PASSWORD=passw123
DB_USER=admin
DB_PASSWORD=admin
```

### Running the API locally
Start the server locally:
```
% poetry run adev runserver -p 8080 --aux-port 8089 src/race_service
```
### Running the API in a wsgi-server (gunicorn)
```
% cd src && poetry run gunicorn race_service:create_app --bind localhost:8080 --worker-class aiohttp.GunicornWebWorker
```
### Running the wsgi-server in Docker
To build and run the api in a Docker container:
```
% docker build -t gcr.io/langrenn-sprint/race-service:latest .
% docker run --env-file .env -p 8080:8080 -d gcr.io/langrenn-sprint/race-service:latest
```
The easier way would be with docker-compose:
```
docker-compose up --build
```
### Running tests
We use [pytest](https://docs.pytest.org/en/latest/) for contract testing.

To run linters, checkers and tests:
```
% nox
```
To run specific test:
```
% nox -s integration_tests -- -k test_create_race_adapter_fails
```
To run tests with logging, do:
```
% nox -s integration_tests -- --log-cli-level=DEBUG
```
