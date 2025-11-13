/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { ChatWidget } from "./chat_widget";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, useRef, App } from "@odoo/owl";
import { templates } from "@web/core/assets";

// Global registry to track widgets
const globalChatRegistry = {
  widgets: new Map(),
};

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    const rootRef = useRef("compiled_view_root");
    let watchInterval = null;

    const getResId = () => this.props.record?.resId;

    const mountChatWidget = async () => {
      if (this.props.record?.resModel !== "chartly.chat") {
        return;
      }

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
