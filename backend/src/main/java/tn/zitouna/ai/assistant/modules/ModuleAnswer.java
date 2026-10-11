package tn.zitouna.ai.assistant.modules;

import java.util.List;

import tn.zitouna.ai.assistant.ChatLink;

/**
 * Answer of a module to a chat question.
 *
 * @param reply template text for the farmer (derja, Arabic script); used as is when no LLM is available
 * @param data  raw module result for the app (charts, tables), or null
 * @param mock  true if the answer is not produced by a trained model yet
 * @param facts compact facts given to the LLM to write a richer reply
 * @param link  button opening a page of the app, or null
 */
public record ModuleAnswer(String reply, Object data, boolean mock, List<Fact> facts, ChatLink link) {

    public ModuleAnswer(String reply, Object data, boolean mock, List<Fact> facts) {
        this(reply, data, mock, facts, null);
    }

    public ModuleAnswer(String reply, Object data, boolean mock) {
        this(reply, data, mock, List.of());
    }

    public static ModuleAnswer stub(String reply) {
        return new ModuleAnswer(reply, null, true);
    }
}
