/** @odoo-module **/

import { registry } from "@web/core/registry";
import {
  Component,
  useState,
  onWillStart,
  onMounted,
  onWillUpdateProps,
} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ChatWidget extends Component {
  static template = "chartly.chat_widget";

  static props = ["*"];

  setup() {
    this.rpc = useService("rpc");
    this.previousChatId = null;

    this.state = useState({
      messages: [],
      inputValue: "",
      isLoading: false,
    });

    // Debug: Log props to see what we're receiving
    console.log("ChatWidget props:", this.props);
    console.log("Chat ID:", this.chatId);

    onWillStart(async () => {
      await this.loadMessages();
      this.previousChatId = this.chatId;
    });

    onMounted(() => {
      this.scrollToBottom();
    });

    onWillUpdateProps(async (nextProps) => {
      const nextChatId = nextProps.record?.resId || nextProps.chatId;
      console.log(
        "Chat ID changing from",
        this.previousChatId,
        "to",
        nextChatId
      );

      if (nextChatId !== this.previousChatId) {
        this.previousChatId = nextChatId;

        // Clear messages immediately for new/different chat
        this.state.messages = [];
        this.state.inputValue = "";

        // Load messages for the new chat
        if (nextChatId) {
          await this.loadMessages(nextChatId);
          this.scrollToBottom();
        }
      }
    });
  }

  get chatId() {
    const id = this.props.record?.resId || this.props.chatId;
    console.log("Getting chatId:", id, "from props:", this.props);
    return id;
  }

  async loadMessages(chatId = null) {
    const id = chatId || this.chatId;
    if (!id) {
      this.state.messages = [];
      return;
    }

    try {
      const result = await this.rpc("/chartly/get_messages", {
        chat_id: id,
      });

      if (result.success) {
        this.state.messages = result.messages;
        this.scrollToBottom();
      }
    } catch (error) {
      console.error("Error loading messages:", error);
    }
  }

  async onSendMessage() {
    if (!this.state.inputValue.trim() || this.state.isLoading) {
      return;
    }

    const chatId = this.chatId;
    if (!chatId) {
      console.error("No chat ID available");
      return;
    }

    const messageContent = this.state.inputValue.trim();
    this.state.inputValue = "";
    this.state.isLoading = true;

    try {
      const result = await this.rpc("/chartly/send_message", {
        chat_id: chatId,
        message_content: messageContent,
      });

      if (result.success) {
        // Add both user and AI messages to state
        if (result.user_message) {
          this.state.messages.push(result.user_message);
        }
        if (result.ai_message) {
          this.state.messages.push(result.ai_message);
        }
        this.scrollToBottom();
      } else {
        console.error("Error sending message:", result.error);
        alert("Error: " + (result.error || "Failed to send message"));
      }
    } catch (error) {
      console.error("Error sending message:", error);
      alert("Error sending message. Please try again.");
    } finally {
      this.state.isLoading = false;
    }
  }

  onKeyPress(ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      this.onSendMessage();
    }
  }

  scrollToBottom() {
    setTimeout(() => {
      const messagesContainer = document.querySelector(".chat-messages");
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 100);
  }
}
