# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.addons.chartly.core.openai import OpenAIClient
import os

class TestOpenAIClientLive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.api_key_file = os.environ.get("OPENAI_API_KEY_FILE")
        with open(self.api_key_file, "r") as f:
            self.api_key = f.read()
        self.client = OpenAIClient(self.api_key)

    def test_chat_completion_live(self):
        messages = [{"role": "user", "content": "Say hello to me."}]
        result = self.client.chat_completion(messages, max_tokens=10, temperature=0)

        # Check API returned success
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        # The content should contain some form of greeting
        self.assertTrue(any(word in result['content'].lower() for word in ['hello', 'hi']))

    def test_chat_completion_with_tools_live(self):
        # Example tools (your actual tools may vary)
        tools = [
            OpenAIClient.create_function_tool(
                name="echo_tool",
                description="Echoes back the input",
                parameters={"input": {"type": "string", "description": "Text to echo"}},
                required= ["input"]
            )
        ]
        messages = [{"role": "user", "content": "Test tool usage"}]
        result = self.client.chat_completion_with_tools(messages, tools, max_tokens=50)

        self.assertTrue(result['success'])
        self.assertIn('content', result)
