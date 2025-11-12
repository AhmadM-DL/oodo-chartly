/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { ChatWidget } from "./chat_widget";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount, useRef, App } from "@odoo/owl";
import { templates } from "@web/core/assets";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    const rootRef = useRef("compiled_view_root");

    onMounted(async () => {
      if (
        this.props.record.resModel === "chartly.chat" &&
        this.props.record.resId
      ) {
        const container = rootRef.el?.querySelector(".o_chat_widget_container");
        if (container && !this.chatWidgetApp) {
          const chatId = this.props.record.resId;
          console.log("Mounting ChatWidget with chatId:", chatId);

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

          // Store the app instance for cleanup
          this.chatWidgetApp = app;
        }
      }
    });

    onWillUnmount(() => {
      if (this.chatWidgetApp) {
        // App has a destroy method that cleans up the component
        this.chatWidgetApp.destroy();
        this.chatWidgetApp = null;
      }
    });
  },
});
