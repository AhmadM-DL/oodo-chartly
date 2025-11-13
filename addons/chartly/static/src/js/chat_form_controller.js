/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { ChatWidget } from "./chat_widget";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, onPatched, useRef, App } from "@odoo/owl";
import { templates } from "@web/core/assets";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    const rootRef = useRef("compiled_view_root");
    this.previousChatId = null;

    const mountChatWidget = async () => {
      if (
        this.props.record.resModel === "chartly.chat" &&
        this.props.record.resId
      ) {
        const container = rootRef.el?.querySelector(".o_chat_widget_container");
        if (container) {
          const chatId = this.props.record.resId;

          // If chat ID changed, destroy old widget and create new one
          if (this.previousChatId !== chatId) {
            if (this.chatWidgetApp) {
              this.chatWidgetApp.destroy();
              this.chatWidgetApp = null;
            }

            console.log("Mounting ChatWidget with chatId:", chatId);
            this.previousChatId = chatId;

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
            this.chatWidgetApp = app;
          }
        }
      }
    };

    onMounted(async () => {
      await mountChatWidget();
    });

    onPatched(async () => {
      await mountChatWidget();
    });

    onWillUnmount(() => {
      if (this.chatWidgetApp) {
        this.chatWidgetApp.destroy();
        this.chatWidgetApp = null;
      }
      this.previousChatId = null;
    });
  },
});
