const ChatService = {
    apiUrl: 'https://api.openai.com/v1/engines/davinci-codex/completions',
    apiKey: null,

    init(apiKey) {
        this.apiKey = apiKey;
    },

    async sendMessage(prompt) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                prompt: prompt,
                max_tokens: 150
            })
        });

        if (!response.ok) {
            throw new Error('Error communicating with OpenAI API');
        }

        const data = await response.json();
        return data.choices[0].text.trim();
    }
};

export default ChatService;