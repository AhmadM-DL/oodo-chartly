/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { ChatWidget } from "./chat_widget";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, onWillStart, useRef, App } from "@odoo/owl";
import { templates } from "@web/core/assets";

// Global registry to track widgets
const globalChatRegistry = {
  widgets: new Map(),
};

// Add a MutationObserver to detect chartly forms early - wrapped for safety
const setupEarlyHiding = () => {
  // Only setup if document.body exists
  if (typeof document === "undefined" || !document.body) {
    return null;
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length) {
        // Check if chartly form is being added
        const hasChartlyForm = document.querySelector(
          ".chartly-chat-form, .o_chat_widget_container"
        );
        if (hasChartlyForm) {
          document.body.classList.add("chartly-chat-view");
          const controlPanel = document.querySelector(".o_control_panel");
          if (controlPanel) {
            controlPanel.style.display = "none";
          }
        }
      }
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
  return observer;
};

// Start observing when DOM is ready
let earlyObserver = null;
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      earlyObserver = setupEarlyHiding();
    });
  } else {
    earlyObserver = setupEarlyHiding();
  }
}

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    const rootRef = useRef("compiled_view_root");
    let watchInterval = null;

    const getResId = () => this.props.record?.resId;

    // Hide control panel immediately for chartly.chat
    const hideControlPanel = () => {
      if (this.props.record?.resModel === "chartly.chat") {
        document.body.classList.add("chartly-chat-view");
        const controlPanel = document.querySelector(".o_control_panel");
        if (controlPanel) {
          controlPanel.style.display = "none";
        }
      }
    };

    // Call immediately in setup
    hideControlPanel();

    // Also hide in onWillStart - runs before mount
    onWillStart(() => {
      hideControlPanel();
    });

    const mountChatWidget = async () => {
      if (this.props.record?.resModel !== "chartly.chat") {
        return;
      }

      // Hide control panel when mounting
      hideControlPanel();

      await new Promise((resolve) => setTimeout(resolve, 100));

      const container = rootRef.el?.querySelector(".o_chat_widget_container");
      if (!container) {
        console.log("⚠️ Container not found");
        return;
      }

      const chatId = getResId();
      if (!chatId) {
        console.log("⚠️ No resId yet");
        return;
      }

      const existingWidget = globalChatRegistry.widgets.get(container);
      if (existingWidget?.chatId === chatId) {
        console.log("✅ Widget already mounted for chat:", chatId);
        return;
      }

      if (existingWidget?.app) {
        console.log("🗑️ Destroying old widget");
        try {
          existingWidget.app.destroy();
        } catch (e) {
          console.error("Error destroying:", e);
        }
      }

      console.log("✨ Mounting ChatWidget for chat:", chatId);

      try {
        const app = new App(ChatWidget, {
          templates,
          env: this.env,
          dev: this.env.debug,
          translatableAttributes: ["data-tooltip"],
          translateFn: this.env._t,
          props: {
            record: this.props.record,
            chatId: chatId,
          },
        });

        await app.mount(container);
        globalChatRegistry.widgets.set(container, { app, chatId });
        console.log("✅ Widget mounted successfully");
      } catch (e) {
        console.error("❌ Error mounting widget:", e);
      }
    };

    const startPolling = () => {
      if (watchInterval) {
        clearInterval(watchInterval);
      }

      let lastResId = getResId();

      watchInterval = setInterval(() => {
        const currentResId = getResId();

        if (currentResId && currentResId !== lastResId) {
          console.log("🔄 ResId changed:", lastResId, "→", currentResId);
          lastResId = currentResId;
          mountChatWidget();
        }
      }, 300);
    };

    onMounted(async () => {
      if (this.props.record?.resModel === "chartly.chat") {
        console.log("🎯 Chat form mounted, resId:", getResId());
        await mountChatWidget();
        startPolling();
      }
    });

    onWillUnmount(() => {
      if (watchInterval) {
        clearInterval(watchInterval);
      }

      // Remove body class when leaving chartly chat
      if (this.props.record?.resModel === "chartly.chat") {
        document.body.classList.remove("chartly-chat-view");
      }

      const container = rootRef.el?.querySelector(".o_chat_widget_container");
      if (container) {
        const widget = globalChatRegistry.widgets.get(container);
        if (widget?.app) {
          try {
            widget.app.destroy();
          } catch (e) {
            console.error("Error on unmount:", e);
          }
          globalChatRegistry.widgets.delete(container);
        }
      }
    });
  },
});
