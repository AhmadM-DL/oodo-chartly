/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ListRenderer.prototype, {
  setup() {
    super.setup();

    // Check if this is the chartly.chat model
    const isChartlyChat = this.props.list?.resModel === "chartly.chat";

    if (!isChartlyChat) {
      return;
    }

    this.action = useService("action");
    this.rpc = useService("rpc");

    // State for dropdown
    this.showSettingsMenu = false;

    // Hide control panel and inject custom header
    const setupCustomHeader = () => {
      document.body.classList.add("chartly-list-view");

      // Hide native control panel
      const controlPanel = document.querySelector(".o_control_panel");
      if (controlPanel) {
        controlPanel.style.display = "none";
      }

      // Check if custom header already exists
      if (document.querySelector(".chartly-list-header")) {
        return;
      }

      // Find the content area to inject header
      const contentArea = document.querySelector(".o_content");
      if (contentArea) {
        const header = this.createCustomHeader();
        contentArea.insertBefore(header, contentArea.firstChild);
      }
    };

    onWillStart(() => {
      // Pre-hide
      document.body.classList.add("chartly-list-view");
    });

    onMounted(() => {
      setupCustomHeader();
      // Also add click handler to close dropdown when clicking outside
      document.addEventListener("click", this.onDocumentClick.bind(this));
    });

    onWillUnmount(() => {
      document.body.classList.remove("chartly-list-view");
      // Remove custom header
      const header = document.querySelector(".chartly-list-header");
      if (header) {
        header.remove();
      }
      document.removeEventListener("click", this.onDocumentClick.bind(this));
    });
  },

  createCustomHeader() {
    const header = document.createElement("div");
    header.className = "chartly-list-header";
    header.innerHTML = `
      <style>
        .chartly-list-header {
          position: sticky;
          top: 0;
          z-index: 100;
          background: #ffffff;
          border-bottom: 1px solid #e0e0e0;
          padding: 12px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        
        .chartly-list-title {
          font-size: 1.3em;
          font-weight: 600;
          color: #333;
          margin: 0;
        }
        
        .chartly-list-header-btn {
          width: 36px;
          height: 36px;
          min-width: 36px;
          min-height: 36px;
          max-width: 36px;
          max-height: 36px;
          padding: 0;
          background: #1a1a1a;
          border: none;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
        
        .chartly-list-header-btn:hover {
          background: #333;
        }
        
        .chartly-list-header-btn svg {
          width: 18px;
          height: 18px;
          fill: white;
        }
        
        .chartly-list-dropdown {
          position: relative;
          display: inline-block;
        }
        
        .chartly-list-dropdown-menu {
          display: none;
          position: absolute;
          right: 0;
          top: 100%;
          margin-top: 8px;
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          min-width: 180px;
          z-index: 1000;
          overflow: hidden;
        }
        
        .chartly-list-dropdown-menu.show {
          display: block;
        }
        
        .chartly-list-dropdown-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 16px;
          cursor: pointer;
          color: #333;
          font-size: 0.9em;
          border: none;
          background: none;
          width: 100%;
          text-align: left;
        }
        
        .chartly-list-dropdown-item:hover {
          background: #f5f5f5;
        }
        
        .chartly-list-dropdown-item.danger {
          color: #dc3545;
        }
        
        .chartly-list-dropdown-item.danger:hover {
          background: #fff5f5;
        }
        
        .chartly-list-dropdown-item svg {
          width: 16px;
          height: 16px;
          fill: currentColor;
        }
        
        /* Confirmation Modal Styles */
        .chartly-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          animation: fadeIn 0.2s ease-out;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        .chartly-modal {
          background: white;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
          max-width: 400px;
          width: 90%;
          animation: slideIn 0.2s ease-out;
        }
        
        @keyframes slideIn {
          from { transform: translateY(-20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        
        .chartly-modal-header {
          padding: 20px 24px 12px;
          border-bottom: 1px solid #eee;
        }
        
        .chartly-modal-title {
          margin: 0;
          font-size: 1.2em;
          font-weight: 600;
          color: #333;
        }
        
        .chartly-modal-body {
          padding: 16px 24px 24px;
          color: #555;
          font-size: 0.95em;
          line-height: 1.5;
        }
        
        .chartly-modal-footer {
          padding: 16px 24px 20px;
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          border-top: 1px solid #eee;
        }
        
        .chartly-modal-btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 0.9em;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .chartly-modal-btn-cancel {
          background: #f5f5f5;
          border: 1px solid #ddd;
          color: #555;
        }
        
        .chartly-modal-btn-cancel:hover {
          background: #eee;
        }
        
        .chartly-modal-btn-danger {
          background: #dc3545;
          border: none;
          color: white;
        }
        
        .chartly-modal-btn-danger:hover {
          background: #c82333;
        }
      </style>
      <div style="display: flex; align-items: center; gap: 12px;">
        <button type="button" class="chartly-list-header-btn chartly-new-chat-btn" title="New Chat">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
        </button>
        <h1 class="chartly-list-title">Chartly Chats</h1>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <div class="chartly-list-dropdown">
          <button type="button" class="chartly-list-header-btn chartly-settings-btn" title="Settings">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/>
            </svg>
          </button>
          <div class="chartly-list-dropdown-menu">
            <button type="button" class="chartly-list-dropdown-item chartly-export-btn">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
              </svg>
              Export Chats
            </button>
            <button type="button" class="chartly-list-dropdown-item danger chartly-delete-all-btn">
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
              </svg>
              Delete All Chats
            </button>
          </div>
        </div>
      </div>
    `;

    // Add event listeners
    const newChatBtn = header.querySelector(".chartly-new-chat-btn");
    const settingsBtn = header.querySelector(".chartly-settings-btn");
    const dropdownMenu = header.querySelector(".chartly-list-dropdown-menu");
    const exportBtn = header.querySelector(".chartly-export-btn");
    const deleteAllBtn = header.querySelector(".chartly-delete-all-btn");

    newChatBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.onNewChat();
    });

    settingsBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenu.classList.toggle("show");
    });

    exportBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenu.classList.remove("show");
      this.onExportChats();
    });

    deleteAllBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdownMenu.classList.remove("show");
      this.onDeleteAllChats();
    });

    return header;
  },

  onDocumentClick(ev) {
    if (!ev.target.closest(".chartly-list-dropdown")) {
      const menu = document.querySelector(".chartly-list-dropdown-menu");
      if (menu) {
        menu.classList.remove("show");
      }
    }
  },

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
  },

  async onExportChats() {
    // Placeholder for export functionality
    alert("Export functionality coming soon!");
  },

  showConfirmModal(title, message, onConfirm) {
    // Remove any existing modal
    const existingModal = document.querySelector(".chartly-modal-overlay");
    if (existingModal) {
      existingModal.remove();
    }

    const modal = document.createElement("div");
    modal.className = "chartly-modal-overlay";
    modal.innerHTML = `
      <div class="chartly-modal">
        <div class="chartly-modal-header">
          <h3 class="chartly-modal-title">${title}</h3>
        </div>
        <div class="chartly-modal-body">
          ${message}
        </div>
        <div class="chartly-modal-footer">
          <button type="button" class="chartly-modal-btn chartly-modal-btn-cancel">
            Cancel
          </button>
          <button type="button" class="chartly-modal-btn chartly-modal-btn-danger">
            Delete
          </button>
        </div>
      </div>
    `;

    // Add event listeners
    const cancelBtn = modal.querySelector(".chartly-modal-btn-cancel");
    const confirmBtn = modal.querySelector(".chartly-modal-btn-danger");
    const modalContent = modal.querySelector(".chartly-modal");

    const closeModal = () => modal.remove();

    cancelBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });
    confirmBtn.addEventListener("click", async () => {
      closeModal();
      await onConfirm();
    });

    // Prevent clicks inside modal from closing it
    modalContent.addEventListener("click", (e) => e.stopPropagation());

    document.body.appendChild(modal);
  },

  async onDeleteAllChats() {
    this.showConfirmModal(
      "Delete All Chats",
      "Are you sure you want to delete ALL chats? This action cannot be undone.",
      async () => {
        try {
          const result = await this.rpc("/chartly/delete_all_chats", {});

          if (result.success) {
            // Refresh the list
            this.action.doAction("chartly.action_chartly_chat");
          }
        } catch (error) {
          console.error("Error deleting all chats:", error);
        }
      }
    );
  },
});
