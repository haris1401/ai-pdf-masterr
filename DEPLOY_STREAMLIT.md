# How to Deploy to Streamlit Community Cloud 🚀

The easiest and best way to deploy your **AI PDF Master** app is using **Streamlit Community Cloud**. It is free and connects directly to your GitHub repository.

## Steps

1.  **Sign In**: Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2.  **New App**: Click the "New app" button.
3.  **Select Repository**:
    *   **Repository**: Choose your new repository (e.g., `your-username/ai-pdf-master`).
    *   **Branch**: `main` (or `master`).
    *   **Main file path**: Enter `app.py`.
4.  **Deploy**: Click "Deploy!".

## Environment Variables (Important for AI) 🔑

If you want the AI features to work online without users typing their key every time:

1.  Go to your App Dashboard on Streamlit.
2.  Click the three dots (`...`) next to your app -> **Settings**.
3.  Go to **Secrets**.
4.  Add your OpenAI API Key like this:
    ```toml
    OPENAI_API_KEY = "sk-proj-..."
    ```
5.  Save!

Your app is now live! 🌐
