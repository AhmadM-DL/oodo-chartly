/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export class ChatWidget extends Component {
    static template = "chartly.chat_widget";
    static props = {
        ...standardWidgetProps,
    };
}

registry.category("view_widgets").add("chat_widget", ChatWidget);
