# Klaus Task Assistant

[![Python](https://img.shields.io/badge/python-3.9+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

Klaus is a cloud-native bot that helps you manage your tasks via natural-language commands. Under the hood it uses:

- **Habitica API** to fetch, create and complete tasks 
- **Google Gemini (Vertex AI)** for NLP: intent classification & task suggestions  
- **RapidFuzz** for fuzzy matching approximate task titles  
- **Firestore** & **ChromaDB** for conversational memory and embeddings  
- **Functions Framework** to deploy as a Cloud Function  
- **python-telegram-bot** for Telegram integration

In the future, it will be much more.

---

## 🚀 Features

1. **Task Status**  
   “What are my tasks for today?” → AI-driven summary & prioritization  
2. **Create Todo**  
   “Remind me to buy milk tomorrow” → creates a Habitica “todo” with due date  
3. **Complete Task**  
   “I finished reading the book” → fuzzy-match title, then mark as complete  
4. **Free-form Chat**  
   Fallback to open-ended conversation when message is unrelated to tasks  
5. **Persistent Memory**  
   Stores conversation history & embeddings to carry context across chats  

---

## 📁 Project Structure

```
.
├── main.py # Cloud Function entrypoint (webhook)
├── ai_assistant.py # Gemini prompt utils: chat, interpret, suggest
├── data
│ └── memory.py # Firestore + ChromaDB for message/embedding storage
├── Dockerfile # Container image for Cloud Build / local dev
├── externals
│ └── habitica_api.py # Habitica HTTP client & helpers
├── handlers
│ └── telegram_handler.py # Telegram request validation & reply
├── requirements.txt # Python dependencies
└── README.md # This documentation
```

---

## 🔧 Prerequisites

- Python 3.9+  
- A Google Cloud project with:
  - Cloud Functions API  
  - Firestore enabled  
  - A (writable) GCS bucket or persistent volume for ChromaDB  
- Habitica account + API token  
- Telegram bot token & secret (or any other simple frontend)

---

## ⚙️ Environment Variables

| Name                          | Description                                        |
| ----------------------------- | -------------------------------------------------- |
| `HABITICA_USER_ID`            | Your Habitica user ID                              |
| `HABITICA_API_TOKEN`          | Your Habitica API token                            |
| `GEMINI_API_KEY`              | Your Vertex AI (Gemini) API key                    |
| `TELEGRAM_BOT_TOKEN`          | Telegram Bot token                                 |
| `TELEGRAM_SECRET_TOKEN`       | Telegram webhook secret                            |
| `TELEGRAM_ALLOWED_CHAT_IDS`   | Comma-separated list of allowed Telegram chat IDs  |
| `DB_PROJECT_ID`               | GCP project ID for Firestore                       |
| `DB_NAME`                     | Firestore database name                            |
| `CHROMA_STORAGE_PATH`         | Path of mounted volume                             |

---

## 🏡 Running Locally

1. **Clone & install**

   ```bash
   git clone https://github.com/your-org/klaus-task-assistant.git
   cd klaus-task-assistant
   pip install -r requirements.txt

2. **Configure environment**

```
export HABITICA_USER_ID="…"
export HABITICA_API_TOKEN="…"
export GEMINI_API_KEY="…"
export TELEGRAM_BOT_TOKEN="…"
export TELEGRAM_SECRET_TOKEN="…"
export TELEGRAM_ALLOWED_CHAT_IDS="123456789"
export DB_PROJECT_ID="my-gcp-project"
export DB_NAME="my-firestore-db"
```

3. **Start Functions Framework**

```
functions-framework --target=webhook --port=8080
```

4. **Test HTTP endpoint**

```
curl -X POST "http://localhost:8080?source=web" \
  -H "Content-Type: application/json" \
  -d '{"message":{"text":"What are my tasks?"}}'
```

5. **Expose and test telegram**

```
ngrok http 8080
# Then point your bot webhook to https://<your-ngrok-url>/?source=telegram
```

---

## ☁️ Deployment (GCP Cloud Build + Cloud Functions)

1. Create a Cloud Build trigger linked to your main branch.

2. Add a cloudbuild.yaml (or use the provided Dockerfile) to build:

```
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

---

## 📖 Usage Examples

- Check tasks

“Do I have any pending dailies?”

- Add a todo

“Preciso enviar relatório amanhã”

- Complete a task

“Já fiz a lição”

- Chat freely

“Qual a previsão do tempo para hoje?”

---

## 🛡️ Best Practices

- Separation of Concerns
- Environment-first: no secrets in code
- Type hints & linting: mypy, ruff compatible
- Graceful error handling: clear user feedback
- Dockerized builds: consistent environments
- CI/CD: automated tests & deploy on merge

---

## ⚖️ License

Distributed under the Apache License. See LICENSE for details.

---

Happy productivity! 🚀