# Klaus Task Assistant

Klaus is a cloud-native, modular Telegram bot that integrates with Habitica’s API and Google’s Gemini (Vertex AI) to manage “todo” and “daily” tasks through natural-language commands. It interprets user messages to check status, create new tasks, or mark tasks as complete—using fuzzy matching to handle approximate titles—and generates AI-driven suggestions and free-form chat responses.

## Project Structure

```
.
├── main.py                      # Entry point for Cloud Functions (HTTP request dispatcher)
├── habitica_api.py              # Module to interact with Habitica API and format tasks
├── ai_assistant.py              # Module to generate suggestions via ChatGPT
├── handlers
│   └── telegram_handler.py      # Telegram-specific request handler
├── requirements.txt             # Python package dependencies
└── README.md                    # Project documentation and best practices
```

## Environment Variables

For the correct functioning of the project, make sure to set the following environment variables:

- **HABITICA_USER_ID**: Your Habitica user ID.
- **HABITICA_API_TOKEN**: Your Habitica API token.
- **GEMINI_API_KEY**: Your API key for Gemini.
- **TELEGRAM_BOT_TOKEN**: The token for your Telegram bot.
- **TELEGRAM_SECRET_TOKEN**: A secret token used to validate incoming Telegram requests.
- **TELEGRAM_ALLOWED_CHAT_IDS**: List of allowed chat IDS that can use this bot on telegram
- **DB_PROJECT_ID**: Name of the project in GCP
- **DB_NAME**: Name of the database
## Best Practices

- **Separation of Concerns**:  
  - Business logic related to Habitica (fetching and formatting tasks) is handled in `habitica_api.py`.  
  - The AI suggestion logic is encapsulated in `ai_assistant.py`.  
  - Telegram-specific processing is isolated in the `handlers/telegram_handler.py` module.
  
- **Modular & Scalable Design**:  
  The dispatcher in `main.py` is designed to handle requests from different sources. By specifying a query parameter (`source`), you can extend the project to support other front-ends beyond Telegram.

- **Error Handling**:  
  Proper error handling is implemented throughout the code. Custom exceptions (if necessary) can include a `status_code` attribute to allow accurate HTTP responses.

- **Environment Security**:  
  - Do not hardcode sensitive values (such as tokens or API keys) in the source code. Use environment variables instead.
  - Ensure environment variables are configured properly in your deployment environment (e.g., Google Cloud Functions, AWS Lambda).

- **Code Readability & Maintainability**:  
  All function and variable names are in English for consistency. Detailed docstrings are provided for each function to enhance code clarity.

## Running Locally

To run the project locally, follow these steps:

1. **Install Dependencies**  
Make sure you have Python installed. Then, run:

```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
Configure the required environment variables. For example, in a Unix-based terminal:

```bash
export HABITICA_USER_ID="your_habitica_user_id"
export HABITICA_API_TOKEN="your_habitica_api_token"
export GEMINI_API_KEY="your_gemini_api_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_SECRET_TOKEN="your_telegram_secret_token"
export TELEGRAM_ALLOWED_CHAT_IDS="your_allowed_telegram_chats"
export DB_PROJECT_ID="your_gcp_project_id"
export DB_NAME="your_database_name_on_gcp"
```

Alternatively, you can use a .env file with a tool like python-dotenv.

3. **Run the Project Using the Functions Framework**
The project is set up to run as an HTTP function with the Functions Framework. Start the server locally by executing:

```bash
functions-framework --target=webhook
```

By default, the server will run on port 8080. You can then send HTTP requests to http://localhost:8080.

4. **Testing the Application**
Example HTTP Request for Testing:
You can test the endpoint using a tool like curl. For instance, to simulate a generic (non-Telegram) request:

```bash
curl -X POST "http://localhost:8080?source=web" \
    -H "Content-Type: application/json" \
    -d '{"message":{"text": "What are my tasks?"}}'
```

5. **Telegram Integration Testing:**
To test the Telegram integration locally, you can use tools such as ngrok to expose your local server to the internet and update your Telegram bot's webhook accordingly.

## Deployment

Follow these steps to deploy the project:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

Set the required environment variables in your deployment environment.

Deploy main.py as your HTTP function (e.g., using Google Cloud Functions or a similar platform).

Configure your Telegram bot to use the deployed function's URL as its webhook.

## Testing

For testing purposes, you can send HTTP requests with the source query parameter set to values other than "telegram". The default behavior assumes a Telegram request if the parameter is absent.

Happy coding!