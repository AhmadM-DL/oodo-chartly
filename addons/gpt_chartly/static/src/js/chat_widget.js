// This file contains the JavaScript code for the chat UI, handling user interactions and message sending.

odoo.define('openai_chat.chat_widget', function (require) {
    "use strict";

    const AbstractWidget = require('web.AbstractWidget');
    const core = require('web.core');
    const rpc = require('web.rpc');

    const _t = core._t;

    const ChatWidget = AbstractWidget.extend({
        template: 'openai_chat.chat_widget',

        events: {
            'click .send-message': 'onSendMessage',
            'keypress .new-message-input': 'onKeyPress',
        },

        init: function (parent) {
            this._super(parent);
            this.messages = [];
            this.chatTitle = '';
        },

        start: function () {
            this.renderChatHistory();
        },

        renderChatHistory: function () {
            const chatHistoryContainer = this.$('.chat-history');
            chatHistoryContainer.empty();
            this.messages.forEach(message => {
                chatHistoryContainer.append(`<div class="message">${message}</div>`);
            });
        },

        onSendMessage: function () {
            const message = this.$('.new-message-input').val();
            if (message) {
                this.messages.push(`You: ${message}`);
                this.renderChatHistory();
                this.$('.new-message-input').val('');
                this.sendMessageToOpenAI(message);
            }
        },

        onKeyPress: function (event) {
            if (event.key === 'Enter') {
                this.onSendMessage();
            }
        },

        sendMessageToOpenAI: function (message) {
            const apiKey = this.getOpenAIKey();
            rpc.query({
                model: 'openai.chat.service',
                method: 'send_message',
                args: [apiKey, message],
            }).then(response => {
                this.messages.push(`OpenAI: ${response}`);
                this.renderChatHistory();
            });
        },

        getOpenAIKey: function () {
            // Fetch the OpenAI API key from the settings
            return this.settings.openai_api_key;
        },
    });

    core.action_registry.add('openai_chat.chat_widget', ChatWidget);
});