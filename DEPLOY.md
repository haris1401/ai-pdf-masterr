# Deployment Instructions

The project is configured for deployment to platforms like Render, Railway, or Heroku.

## Prerequisites

-   A GitHub repository with this code.
-   An account on Render/Railway/Heroku.

## Deploy to Render (Recommended)

1.  Push this code to a GitHub repository.
2.  Log in to [Render](https://render.com/).
3.  Click **New +** -> **Web Service**.
4.  Connect your GitHub repository.
5.  Render will automatically detect the `requirements.txt` and `Procfile`.
6.  Set the **Build Command** to: `pip install -r requirements.txt`
7.  Set the **Start Command** to: `uvicorn main:app --host 0.0.0.0 --port $PORT`
    -   Note: We created a `main.py` in the root that imports the backend app.
8.  Click **Create Web Service**.

## Deploy to Vercel

1.  Push this code to a GitHub repository.
2.  Log in to [Vercel](https://vercel.com/).
3.  Import the repository.
4.  Vercel should detect the Python project.
5.  Ensure the **Root Directory** is set to `.` (current directory).
6.  Deploy.

## Deploy to Heroku

1.  Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
2.  Login: `heroku login`
3.  Create an app: `heroku create`
4.  Deploy: `git push heroku main`

## Notes

-   **Database**: The current configuration uses SQLite (`ai_console.db`). On platforms like Render/Heroku, the filesystem is ephemeral, meaning the database will be reset on every deployment/restart. For production, switch to a persistent database like PostgreSQL.
-   **Environment Variables**: If you use API keys (e.g., OpenAI), set them in the platform's environment variable settings.
