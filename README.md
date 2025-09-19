


# Social Media Crawler  

This project is designed for **crawling data from various social media platforms** using a set of specialized crawler modules.  

---
## Use Cases  

The **Social Crawlers Raased** project was used for advanced social media data collection and internal content visualization.  
Key scenarios included:  

- Collecting **posts, comments, likes, and reposts** from multiple social media platforms.  
- Displaying identical copies of posts inside the internal system, replicating their original look.  
- Showing detailed context for each post:  
  - The **author** who published it  
  - The **platform** (e.g., Twitter, Facebook, Instagram, etc.)  
  - The **full post content** with media, as it appears on the real social network  
- Providing analysts and managers with a unified interface for monitoring cross-platform engagement.
---
## Features  

- Collects all available posts from supported platforms.  
- Support for multiple platforms: Twitter, Facebook, Instagram, Medium, Reddit, TikTok

- Flexible architecture: each crawler runs independently, allowing you to scale and adapt the project to specific needs.  
- REST API interface built with **FastAPI** for easy integration with other services.  

---

## Installation  

### 1. Clone the repository  
```bash
git clone https://github.com/your-username/social-media-crawler.git

cd social-media-crawler
```
### 2. Install enviroment:
```
in backend/app, create .env file(temp in THIS), then:

`cd backend/app`

`poetry install`

`poetry run uvicorn app.main:app --reload`

`poetry run alembic revision --autogenerate -m "DO SOMETHING"`

`poetry run alembic upgrade head`
```
### 3. Install dependencies:
```
pip install -r requirements.txt
```
## Run App
### 1. Start the FastAPI Application  
```bash
uvicorn app.main:app --reload
```

### 2. Run a Crawler

Each crawler can be started with a dedicated command, where you specify the desired social media engine.

```bash 
python app/crawlers/crawlers.py twitter
```

If you pass an invalid engine name, the program will terminate with an error message:

```bash 
Invalid SmmEngine. Exiting...
```

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
