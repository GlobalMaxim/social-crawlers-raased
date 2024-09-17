# Installation:
in backend/app, create .env file(temp in THIS), then:


`cd backend/app`

`poetry install`

`poetry run uvicorn app.main:app --reload`

`poetry run alembic revision --autogenerate -m "DO SOMETHING"`

`poetry run alembic upgrade head`


### Run RabbitMQ in Docker
`docker run --rm -it -p 15672:15672 -p 5672:5672`

rabbitmq:3-management


### VS Code PyTest Debug launch.json:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app"
            ],
            "jinja": true,
            "justMyCode": true
        },
        {
            "name": "PyTest",
            "type": "python",
            "request": "launch",
            "stopOnEntry": false,
            "module": "pytest",
            "args": [
                "-sv"
            ],
            "cwd": "${workspaceRoot}",
            "env": {},
            "envFile": "${workspaceRoot}/.env",
        }
    ]
}
```