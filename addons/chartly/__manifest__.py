{
    "name": "Chartly",
    "version": "1.0",
    "category": "Tools",
    "summary": "Odoo module for integrating OpenAI chat functionality.",
    "description": "This module allows users to interact with OpenAI's API through a chat interface within Odoo. Users can save their OpenAI API key and view chat history.",
    "author": "Your Name",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        # "views/menu_views.xml",
        "views/openai_settings_views.xml",
        "views/chat_conversation_views.xml",
        "views/chat_message_views.xml",
        "data/default_data.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False
}