{
    "name": "Chartly",
    "version": "1.0",
    "category": "Utility",
    "summary": "Generate charts and visualizations using natural language prompts.",
    "description": "This module provides functionalities to generate charts and visualizations based on user input and natural language prompts.",
    "author": "Ahmad Mustapha, Ali Sahili",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/chat.xml",
        "views/res_config_settings_view.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "chartly/static/src/js/chat_widget.js",
            "chartly/static/src/js/chat_from_controller.js",
            "chartly/static/src/xml/chat_widget.xml",
        ],
    },
    "demo": [
        "demo/demo_data.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}