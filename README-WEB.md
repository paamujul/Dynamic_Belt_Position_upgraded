# Dynamic Belt Position Web Interface

This directory contains the web interface built to interact with the Dynamic Belt Position python pipeline.

## Features
- A **Next.js** frontend built with React and Tailwind CSS.
- A **FastAPI** Python backend that processes the master XSENSOR CSV file and triggers the pipeline.

## How to Run Locally

### 1. Start the Python Backend API
The backend requires `fastapi`, `uvicorn`, and `python-multipart` to handle file uploads and serve the API.

```bash
# Install dependencies
pip install fastapi uvicorn python-multipart

# Start the API server
python src/web_api/api.py
```
The FastAPI server will start on `http://localhost:8000`.

### 2. Start the Next.js Frontend
Open a new terminal window and navigate to the `frontend` folder:

```bash
cd frontend

# Install Node modules
npm install

# Start the development server
npm run dev
```
The web interface will be available at `http://localhost:3000`.

## Vercel Deployment Note
While the **frontend Next.js** app is fully deployable onto Vercel out of the box, deploying the **Python pipeline backend** to Vercel Serverless Functions has significant limitations:
1. **Read-Only Filesystem**: Vercel Serverless functions can only write to the `/tmp` directory. The python pipeline heavily relies on saving persistent files to `templates/DATA/`. 
2. **Library Size Limits**: Vercel has a 250MB unzipped limit on Python Serverless Functions, which is frequently exceeded when deploying large frameworks like `pandas`, `scikit-learn`, `numpy`, and `scipy`.

**Recommendation**: 
Deploy the `frontend` folder to Vercel as a standard Next.js project. For the python backend, deploy the root repository to a Virtual Private Server (VPS) or a platform like **Render** or **Heroku** which natively supports background workers and writable disk volumes. Update the Next.js `fetch` URL in `src/app/page.tsx` to point to the production deployed Python backend URL.
