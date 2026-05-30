# Anki Biochemistry Generator

This full-stack application automates the generation of Anki flashcard decks for medical biochemistry. It extracts compounds and pathways from text/PDF documents and generates highly visual Anki cards.

## Features

1. **Standard Compounds**: Parses text for chemical names, retrieves SMILES strings via Gemini, generates 2D structural images using `RDKit`, and packages them into Anki cards.
2. **Pathway Occlusion**: Extracts entire metabolic pathways into directed graphs, renders them via `Graphviz`, extracts precise bounding box coordinates for each node, and uses `Pillow` to create image-occlusion flashcards.

## Architecture

* **Frontend**: React application built with Vite and TailwindCSS. Easily deployed to GitHub Pages.
* **Backend**: Python FastAPI application using RDKit, Graphviz, Pillow, and Genanki. Containerized via Docker for easy deployment to Google Cloud Run.

---

## Deployment Tutorial

### 1. Backend: Deploying to Google Cloud Run

Google Cloud Run is a perfect service for this backend because it directly runs Docker containers and scales to zero when not in use, making it very cheap (often free).

**Prerequisites:**
* A Google Cloud Platform (GCP) account.
* The Google Cloud CLI (`gcloud`) installed on your machine.
* Docker installed on your machine.

**Steps:**

1. **Authenticate and configure GCP:**
   Open your terminal and run:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs in GCP:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable artifactregistry.googleapis.com
   ```

3. **Build the Docker Image:**
   Navigate to the `backend` folder and build the image, tagging it for Google Artifact Registry (replace `REGION` like `us-central1` and `PROJECT_ID`):
   ```bash
   cd backend
   docker build -t gcr.io/YOUR_PROJECT_ID/anki-biochem-backend .
   ```

4. **Push the Image to GCP:**
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/anki-biochem-backend
   ```

5. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy anki-biochem-backend \
     --image gcr.io/YOUR_PROJECT_ID/anki-biochem-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 1Gi
   ```
   *Note: We allocate `1Gi` of memory because RDKit and image processing can be slightly memory-intensive.*

6. **Save your Backend URL:**
   Once deployed, the terminal will output a Service URL (e.g., `https://anki-biochem-backend-xxxxx-uc.a.run.app`). Save this URL.

---

### 2. Frontend: Deploying to GitHub Pages

**Prerequisites:**
* A GitHub account.
* Git installed on your machine.

**Steps:**

1. **Update the Backend URL in the Frontend:**
   In the `frontend` folder, create a file named `.env.production`:
   ```env
   VITE_BACKEND_URL=https://YOUR_CLOUD_RUN_URL/generate
   ```
   *(Replace `YOUR_CLOUD_RUN_URL` with the URL you got in step 6 above).*

2. **Configure Vite for GitHub Pages:**
   Ensure `vite.config.js` has `base: './'` or the name of your repository if deploying to a subpath (e.g., `base: '/my-repo-name/'`).

3. **Deploy using gh-pages:**
   In the `frontend` directory, install the `gh-pages` package:
   ```bash
   npm install gh-pages --save-dev
   ```

   Add these scripts to your `frontend/package.json`:
   ```json
   "scripts": {
     "predeploy": "npm run build",
     "deploy": "gh-pages -d dist",
     ...
   }
   ```

4. **Run the deployment:**
   ```bash
   npm run deploy
   ```

   Your React app will now be compiled and pushed to the `gh-pages` branch of your repository. Go to your repository settings on GitHub, navigate to "Pages", and ensure it is being served from the `gh-pages` branch.

Your full-stack application is now fully online! You can navigate to your GitHub Pages URL, enter your Gemini API key, upload a PDF, and generate Anki decks entirely in the cloud.
