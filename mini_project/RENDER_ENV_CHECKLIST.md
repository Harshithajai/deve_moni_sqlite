# Environment Variables Checklist for Deployment

This checklist outlines all the environment variables needed when deploying DevCare (FastAPI backend + PostgreSQL on Render, React frontend on Netlify).

---

## 1. Render Backend Service (Environment Tab)

Set these variables in the **Environment** tab of your Render Web Service:

| Variable name | Where the value comes from | Notes |
| :--- | :--- | :--- |
| `DATABASE_URL` | Render PostgreSQL database service | Copy the **Internal Database URL** from your Render PostgreSQL instance page. Do **not** use your local SQLite/MySQL URL or external URL. Render automatically resolves internal database connections via this URL. |
| `JWT_SECRET` | Newly generated random string (see generated key in task report) | Generate a dedicated, cryptographically secure 48+ byte random string specifically for Render production. Never reuse default or development secrets. |
| `JWT_ALGORITHM` | Fixed standard configuration value | Set to `HS256`. Must match the algorithm used for encoding and decoding authentication tokens. |
| `GROQ_API_KEY` | Groq Console or local `.env` | Copy the active Groq API key from your Groq developer account dashboard (or your local `.env`). Required for AI / LLM features. |
| `GROQ_MODEL` | Local `.env` configuration | Copy the model identifier from your local `.env` (e.g., `openai/gpt-oss-20b` or `llama-3.3-70b-versatile`). |
| `LLM_FALLBACK_RULE_BASED` | Local `.env` configuration | Set to `true` to enable rule-based fallback if Groq API rate limits or errors occur. |
| `LLM_TIMEOUT_SECONDS` | Local `.env` configuration | Set to `30` (or your configured timeout in seconds) to manage request timeouts for LLM operations. |
| `CORS_ORIGINS` | Netlify site deployment URL | Provide your production Netlify site URL (e.g., `https://your-site.netlify.app`). Multiple origins can be separated by commas. **Do not include a trailing slash**. |
| `PYTHON_VERSION` | Fixed Render runtime version | Set to `3.12.7`. Ensures Render builds the application with Python 3.12 matching project requirements. |

---

## 2. Netlify Frontend Site (Environment Variables)

Set this variable in your Netlify Site configuration under **Site configuration > Environment variables**:

| Variable name | Where the value comes from | Notes |
| :--- | :--- | :--- |
| `VITE_API_URL` | Render Web Service URL | Set to your live Render backend URL (e.g., `https://devcare-api.onrender.com`). **Do not include a trailing slash**. Vite embeds this during build time for Axios API requests. |
