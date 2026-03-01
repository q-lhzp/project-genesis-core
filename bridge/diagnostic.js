"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = register;
function register(api) {
    api.registerHook("llm_input", (event) => {
        // Diagnostic hook - inspect payload before API call
        console.log(">>> DIAGNOSTIC HOOK START <<<");
        console.log("Event keys:", Object.keys(event).join(", "));
        // Check tools in payload
        if (event.payload && event.payload.tools) {
            const toolNames = event.payload.tools.map((t) => t.name);
            console.log("Payload Tools:", toolNames.join(", "));
            event.payload.tools.forEach((t, i) => {
                const hasValidParams = t.parameters &&
                                       typeof t.parameters === 'object' &&
                                       Object.keys(t.parameters).length > 0;
                if (!hasValidParams) {
                    console.log(`TOOL MISSING PARAMETERS: Index ${i}, Name ${t.name}`);
                }
            });
        }
        // Check messages
        if (event.payload && event.payload.messages) {
            const systemMsg = event.payload.messages.find((m) => m.role === 'system');
            if (systemMsg) {
                console.log("System message found, length:", systemMsg.content ? systemMsg.content.length : 0);
            }
        }
        return event;
    });
}
