# 📊 Chartly

![Chartly Screenshot](./assets/Odoo Chartly.png)

## 📝 Description

**Chartly** is a powerful utility module designed to retrieve data, generate charts and visualizations using natural language prompts. This module provides functionalities to generate charts and visualizations based on user input, making data analysis more accessible and intuitive.

## ✨ Features

- **Natural Language Processing**: Retrieve data and Generate charts by simply describing what you want to see.
- **Seamless Integration**: Built to work with Odoo's existing `account` module. We are working on adding more modules.
- **Interactive Visualizations**: Create dynamic charts that help in better decision making.
- **Chat Interface with Agentic AI**: Interact with your data through a chat interface.

## 🛠️ Development
1.  Clone this repository dev branch.
    ```bash
    git clone -b dev <repository-url> oodo-chartly
    ```
2. Create a secrets folder
3. Create openai_api_key.txt file and add your OpenAI API key.
4. Run docker compose -f docker-compose.dev.yml up -d

## 📦 Odoo Dependencies

- `base`
- `web`
- `account`

## 📝 Contributing

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them.
4.  Push your changes to your fork.
5.  Create a pull request.

## TODO

- [ ] Profile latency
- [ ] Better Interface
- [ ] Better Chart Quality
- [ ] Better LLM prompts and evalautions

## 📝 License

This project is licensed under the MIT License
