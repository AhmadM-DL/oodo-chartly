# Odoo OpenAI Chat Module

This project is an Odoo module that integrates OpenAI's API for chat functionalities. It allows users to manage chat conversations and settings, including an immutable OpenAI API key.

## Project Structure

```
odoo-openai-chat
├── docker-compose.yml       # Defines services for Odoo and PostgreSQL
├── Dockerfile               # Builds the Docker image for Odoo
├── addons
│   └── openai_chat
│       ├── __init__.py     # Initializes the Odoo module
│       ├── __manifest__.py # Metadata for the Odoo module
│       ├── models
│       │   ├── __init__.py
│       │   ├── openai_settings.py  # Model for OpenAI settings
│       │   ├── chat_conversation.py # Model for chat conversations
│       │   └── chat_message.py      # Model for chat messages
│       ├── controllers
│       │   ├── __init__.py
│       │   └── chat_controller.py   # Handles chat logic
│       ├── views
│       │   ├── openai_settings_views.xml # View for OpenAI settings
│       │   ├── chat_conversation_views.xml # View for chat conversations
│       │   ├── chat_message_views.xml # View for chat messages
│       │   └── menu_views.xml       # Menu structure for the module
│       ├── security
│       │   ├── ir.model.access.csv  # Access control rules
│       │   └── security.xml         # Security groups and permissions
│       ├── static
│       │   └── src
│       │       ├── js
│       │       │   ├── chat_widget.js    # JavaScript for chat UI
│       │       │   └── chat_service.js   # JavaScript for OpenAI API interaction
│       │       └── xml
│       │           └── chat_templates.xml # XML templates for chat UI
│       └── data
│           └── default_data.xml      # Default data for the module
└── README.md                       # Documentation for the project
```

## Setup Instructions

1. **Clone the Repository**
   ```
   git clone <repository-url>
   cd odoo-openai-chat
   ```

2. **Build and Run the Docker Containers**
   ```
   docker-compose up --build
   ```

3. **Access Odoo**
   Open your web browser and navigate to `http://localhost:8069`.

4. **Install the Module**
   - Go to the Apps menu in Odoo.
   - Update the app list.
   - Search for "OpenAI Chat" and install the module.

## Usage Guidelines

- **Settings Tab**: The OpenAI API key can be set here. Note that this setting is immutable.
- **Chat Tab**: View historical chats and create new ones. Each chat displays the title and date.
- **Chat UI**: Interact with the chat by sending messages. Responses from OpenAI will be displayed in the chat history.

## Best Practices

This module adheres to SOLID principles and follows DRY practices to ensure maintainability and scalability. 

## License

This project is licensed under the MIT License. See the LICENSE file for more details.