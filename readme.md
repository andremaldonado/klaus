# Klaus Task Assistant

[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Table of Contents

 - [📝 What it is](#-what-it-is)
 - [🚀 Features](#-features)
 - [📁 Project Structure](#-project-structure)
 - [🔧 Prerequisites](#-prerequisites)
 - [⚙️ Environment Variables](#️-environment-variables)
 - [🏡 Running Locally](#-running-locally)
 - [🐳 Docker](#-docker)
 - [☁️ Deployment](#️-deployment-gcp-cloud-build--cloud-functions)
 - [📖 Usage Examples](#-usage-examples)
 - [🛡️ Best Practices](#️-best-practices)
 - [🤝 Contributing](#-contributing)
 - [⚖️ License](#️-License)

## 📝 What it is

Klaus is a cloud-native bot that helps you manage your life via natural-language commands. 

Under the hood it uses:

- **Habitica API** to fetch, create and complete tasks 
- **Google Gemini** for conversation
- **RapidFuzz** for fuzzy matching approximate task titles  
- **Firestore** & **ChromaDB** for conversational memory, lists management, embeddings and more
- **Functions Framework** to deploy as a Cloud Function  
- **Google Calendar API** to fecth and create events

In the future, it will be much more.

## 🚀 Features

1. **Task Status**  
2. **Create Todo**  
3. **Complete Task**  
4. **List calendar events**  
5. **Create calendar events**  
6. **Manage lists** 
7. **Free-form Chat**  
8. **Persistent Memory**  
9. **Server messages for other agents**

## 📁 Project Structure

```
.
├── src/klaus
│   ├── auth
|   │    ├── auth_handler.py                   # OAuth2 Google authorization handler
|   │    └── credentials.py                    # Sanitize IDs, extract email, load OAuth credentials.
│   ├── data
│   |    ├── list.py                           # Firestore-based handlers for list management.
│   |    ├── memory.py                         # Firestore + ChromaDB for message/embedding storage
│   |    ├── message.py                        # Firestore server sent messages
│   |    ├── user.py                           # Helper retrieves user document from Firestore collection.
│   |    └── client.py                         # Firestore client initialization via environment variables.
│   ├── externals
│   |    ├── calendar_api.py                   # Google Calendar client & helpers
│   |    └── habitica_api.py                   # Habitica HTTP client & helpers for those who use habitica as task manager
│   ├── handlers
│   |    ├── ai_assistant.py                   # Intent detection, date parsing, responses.
│   |    ├── calendar.py                       # Handlers for listing and creating calendar events.
│   |    ├── general.py                        # Handlers for general chat logic for memory and intents.
│   |    ├── list.py                           # Handlers for managing lists
│   |    ├── task.py                           # Handlers for managing user tasks creation, status, and completion.
│   |    └── utils.py                          # Date parsing and message storage utilities.
|   ├── tests
│   |    ├── test_check_intents.py             # Tests intent detection for calendar and tasks.
│   |    └── test_interpret_user_message.py    # Tests interpret_user_message for task and event parsing.
|   ├── main.py                                # Webhook handling auth and dispatching chatbot intents.
|   └── schemas.py                             # Pydantic schemas for request validation.
├── .gitignore                                 # You know this file
├── Dockerfile                                 # Docker image for Python webhook application.
├── LICENSE                                    # License file
├── readme.md                                  # The file you are reading
└── requirements.txt                           # List of required Python dependencies for project.
```

## 🔧 Prerequisites

- Python 3.9+  
- A Google Cloud project with:
  - Cloud Functions API  
  - Firestore enabled  
  - A (writable) GCS bucket or persistent volume for ChromaDB  

## ⚙️ Environment Variables

| Name                          | Description                                        |
| ----------------------------- | -------------------------------------------------- |
| `ALLOWED_EMAILS`              | E-mails that can use the app                       |
| `CHROMA_STORAGE_PATH`         | Path of mounted volume                             |
| `CORS_ALLOW_ORIGIN`           | Origins alloweed for this API                      |
| `DB_PROJECT_ID`               | GCP project ID for Firestore                       |
| `DB_NAME`                     | Firestore database name                            |
| `ENVIRONMENT`                 | Environment in which the app is running            |
| `GEMINI_API_KEY`              | Your Vertex AI (Gemini) API key                    |
| `GOOGLE_CLIENT_ID`            | Cliend ID for OAuth                                |
| `GOOGLE_CLIENT_SECRET`        | Secret for OAuth                                   |
| `GOOGLE_REDIRECT_URI`         | Redirect URI of google auth key                    |
| `TIMEZONE`                    | Timezone of your preference                        |


## 🏡 Running Locally

1. **Clone & install**

```bash
git clone https://github.com/your-org/klaus-task-assistant.git
cd klaus-task-assistant
pip install --upgrade pip
pip install -r requirements.txt
```

2. **Configure environment**

```bash
export GEMINI_API_KEY="…"
export DB_PROJECT_ID="…"
export DB_NAME="…"
export ENVIRONMENT="…"
export ALLOWED_EMAILS="…"
export GOOGLE_CLIENT_ID="…"
export GOOGLE_CLIENT_SECRET="…"
export FIRESTORE_EMULATOR_HOST="…"
```

3. **Start Functions Framework**

```bash
cd src/klaus
functions-framework --target=webhook --port=8080
```

4. **Test HTTP endpoint**

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ID_TOKEN>" \
  -d '{"text":"What are my tasks?"}'
```

## 🐳 Docker

Build and run locally with Docker:

```bash
docker build -t "klaus:Dockerfile" .
docker run \
    -e GEMINI_API_KEY="..." \
    -e GOOGLE_CLIENT_ID="...apps.googleusercontent.com" \
    -e GOOGLE_CLIENT_SECRET="..." \
    -e FIRESTORE_EMULATOR_HOST="..." \
    -e DB_PROJECT_ID="..." \
    -e DB_NAME="..." \
    -e ALLOWED_EMAILS="...@gmail.com" \
    -e ENVIRONMENT="dev" \
    --network=host \
    -p 8080:8080 \
    klaus:Dockerfile
```

## ☁️ Deployment (GCP Cloud Build + Cloud Functions)

1. Create a Cloud Build trigger linked to your main branch.

2. Add a cloudbuild.yaml (or use the provided Dockerfile) to build:

```bash
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: [ 'build', '-t', 'gcr.io/$PROJECT_ID/klaus-assistant', '.' ]
  - name: 'gcr.io/cloud-builders/gcloud'
    args: [ 'functions', 'deploy', 'webhook',
            '--region=us-central1',
            '--runtime=python39',
            '--trigger-http',
            '--allow-unauthenticated',
            '--entry-point=webhook',
            '--image', 'gcr.io/$PROJECT_ID/klaus-assistant' ]
images:
  - 'gcr.io/$PROJECT_ID/klaus-assistant'
```

3. On each merge to main, Cloud Build will rebuild the container and redeploy.

## 📖 Usage Examples

- Check tasks: _“Do I have any pending dailies?”_
- Add a todo: _“Preciso enviar relatório amanhã”_
- Complete a task: _“Já fiz a lição”_
- Chat freely: _“Qual a previsão do tempo para hoje?”_
- Create an event on your calendar: _"Vou noo shopping hoje às 18:00. Crie este evento na minha agenda."_

## 🛡️ Best Practices

- Separation of Concerns
- Environment-first: no secrets in code
- Type hints & linting: mypy, ruff compatible
- Graceful error handling: clear user feedback
- Dockerized builds: consistent environments
- CI/CD: automated tests & deploy on merge

## 🤝 Contributing

Contributions are welcome!  

1. Fork the repo  
2. Create a feature branch (`git checkout -b feature/xyz`)  
3. Commit your changes (`git commit -am 'Add xyz'`)  
4. Push to the branch (`git push origin feature/xyz`)  
5. Open a Pull Request  

## ⚖️ License

This project is licensed under the Apache License. See [LICENSE](./LICENSE) for details.

Happy productivity! 🚀