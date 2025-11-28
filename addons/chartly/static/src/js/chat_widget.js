/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ChatWidget extends Component {
  static template = "chartly.chat_widget";

  static props = ["*"];

  setup() {
    this.rpc = useService("rpc");
    this.action = useService("action");

    this.state = useState({
      messages: [],
      inputValue: "",
      isLoading: false,
      totalCost: 0,
      chatTitle: "",
      createdAt: "",
      showMenu: false,
      showConfirmModal: false,
      confirmModalTitle: "",
      confirmModalMessage: "",
      confirmModalAction: null,
    });

    console.log("ChatWidget setup - Chat ID:", this.chatId);

    // Hide control panel immediately to prevent flash
    this.hideControlPanel();

    onWillStart(async () => {
      console.log(
        "ChatWidget onWillStart - loading messages for chat:",
        this.chatId
      );
      this.hideControlPanel();
      await this.loadChatInfo();
      await this.loadMessages();
    });

    onMounted(() => {
      console.log("ChatWidget mounted");
      this.hideControlPanel();
      this.scrollToBottom();
      // Close dropdown when clicking outside
      document.addEventListener("click", this.onDocumentClick.bind(this));
    });
  }

  hideControlPanel() {
    // Add body class for CSS targeting
    document.body.classList.add("chartly-chat-view");

    // Also directly hide control panel
    const controlPanel = document.querySelector(".o_control_panel");
    if (controlPanel) {
      controlPanel.style.display = "none";
    }
  }

  get chatId() {
    const id = this.props.record?.resId || this.props.chatId;
    console.log("Getting chatId:", id, "from props:", this.props);
    return id;
  }

  get formattedTotalCost() {
    return this.state.totalCost.toFixed(5);
  }

  async loadChatInfo() {
    const id = this.chatId;
    if (!id) return;

    try {
      const result = await this.rpc("/chartly/get_chat_info", {
        chat_id: id,
      });

      if (result.success) {
        this.state.chatTitle = result.title || "";
        this.state.createdAt = result.created_at || "";
        this.state.totalCost = result.total_cost || 0;
      }
    } catch (error) {
      console.error("Error loading chat info:", error);
    }
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
        this.state.totalCost = result.total_cost || 0;
        this.scrollToBottom();
      }
    } catch (error) {
      console.error("Error loading messages:", error);
    }
  }

  // Navigation methods
  onGoHome() {
    this.action.doAction("chartly.action_chartly_chat");
  }

  async onNewChat() {
    try {
      const result = await this.rpc("/chartly/create_chat", {
        title: "New Chat",
      });

      if (result.success) {
        this.action.doAction({
          type: "ir.actions.act_window",
          res_model: "chartly.chat",
          res_id: result.chat_id,
          view_mode: "form",
          views: [[false, "form"]],
          target: "current",
        });
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  }

  // Dropdown menu methods
  onToggleMenu(ev) {
    ev.stopPropagation();
    this.state.showMenu = !this.state.showMenu;
  }

  onDocumentClick(ev) {
    if (!ev.target.closest(".chartly-dropdown")) {
      this.state.showMenu = false;
    }
  }

  async onDuplicateChat() {
    this.state.showMenu = false;
    const chatId = this.chatId;
    if (!chatId) return;

    try {
      const result = await this.rpc("/chartly/duplicate_chat", {
        chat_id: chatId,
      });

      if (result.success) {
        this.action.doAction({
          type: "ir.actions.act_window",
          res_model: "chartly.chat",
          res_id: result.chat_id,
          view_mode: "form",
          views: [[false, "form"]],
          target: "current",
        });
      }
    } catch (error) {
      console.error("Error duplicating chat:", error);
    }
  }

  async onDeleteChat() {
    this.state.showMenu = false;
    const chatId = this.chatId;
    if (!chatId) return;

    this.showConfirmModal(
      "Delete Chat",
      "Are you sure you want to delete this chat? This action cannot be undone.",
      async () => {
        try {
          const result = await this.rpc("/chartly/delete_chat", {
            chat_id: chatId,
          });

          if (result.success) {
            this.action.doAction("chartly.action_chartly_chat");
          }
        } catch (error) {
          console.error("Error deleting chat:", error);
        }
      }
    );
  }

  // Confirmation modal methods
  showConfirmModal(title, message, action) {
    this.state.confirmModalTitle = title;
    this.state.confirmModalMessage = message;
    this.state.confirmModalAction = action;
    this.state.showConfirmModal = true;
  }

  onConfirmModalCancel() {
    this.state.showConfirmModal = false;
    this.state.confirmModalAction = null;
  }

  async onConfirmModalConfirm() {
    this.state.showConfirmModal = false;
    if (this.state.confirmModalAction) {
      await this.state.confirmModalAction();
    }
    this.state.confirmModalAction = null;
  }

  // Title editing methods
  onTitleInput(ev) {
    this.state.chatTitle = ev.target.value;
  }

  async onTitleBlur(ev) {
    await this.saveTitle();
  }

  onTitleKeyPress(ev) {
    if (ev.key === "Enter") {
      ev.preventDefault();
      ev.target.blur();
    }
  }

  async saveTitle() {
    const chatId = this.chatId;
    if (!chatId) return;

    try {
      await this.rpc("/chartly/update_title", {
        chat_id: chatId,
        title: this.state.chatTitle,
      });
    } catch (error) {
      console.error("Error saving title:", error);
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

    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      content: messageContent,
      sender: "user",
      created_at: new Date().toLocaleString(),
      cost: 0,
    };
    this.state.messages.push(userMessage);

    // Add loading message placeholder
    const loadingMessage = {
      id: Date.now() + 1,
      content: "",
      sender: "ai",
      created_at: "",
      isLoading: true,
      cost: 0,
    };
    this.state.messages.push(loadingMessage);
    this.scrollToBottom();

    try {
      const result = await this.rpc("/chartly/send_message", {
        chat_id: chatId,
        message_content: messageContent,
      });

      // Remove loading message
      const loadingIndex = this.state.messages.findIndex((m) => m.isLoading);
      if (loadingIndex !== -1) {
        this.state.messages.splice(loadingIndex, 1);
      }

      if (result.success) {
        // Add AI message to state (user message already shown)
        if (result.ai_message) {
          this.state.messages.push(result.ai_message);
        }
        if (result.total_cost !== undefined) {
          this.state.totalCost = result.total_cost;
        }
        this.scrollToBottom();
      } else {
        console.error("Error sending message:", result.error);
        this.state.messages.push({
          id: Date.now() + 2,
          content: "Error: " + (result.error || "Failed to send message"),
          sender: "ai",
          created_at: new Date().toLocaleString(),
          cost: 0,
        });
      }
    } catch (error) {
      console.error("Error sending message:", error);
      // Remove loading message
      const loadingIndex = this.state.messages.findIndex((m) => m.isLoading);
      if (loadingIndex !== -1) {
        this.state.messages.splice(loadingIndex, 1);
      }
      this.state.messages.push({
        id: Date.now() + 2,
        content: "Sorry, there was an error processing your request.",
        sender: "ai",
        created_at: new Date().toLocaleString(),
        cost: 0,
      });
    } finally {
      this.state.isLoading = false;
      this.scrollToBottom();
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
      // Try to find the last message and scroll it to the top of the view
      const messages = document.querySelectorAll(".message-wrapper");
      if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        lastMessage.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }

      // Fallback: try various scrollable containers
      const selectors = [
        ".chat-messages-scrollable",
        ".chat-messages",
        ".o_content",
        ".o_form_sheet_bg",
      ];

      for (const selector of selectors) {
        const container = document.querySelector(selector);
        if (container && container.scrollHeight > container.clientHeight) {
          container.scrollTop = container.scrollHeight;
          break;
        }
      }
    }, 200);
  }

  updateHeaderCost() {
    const costElement = document.querySelector(".chartly-cost-value");
    if (costElement) {
      costElement.textContent = this.state.totalCost.toFixed(5);
    }
  }
}
