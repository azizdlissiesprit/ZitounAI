package tn.zitouna.ai.assistant.modules;

/**
 * Answer of a module to a chat question.
 *
 * @param reply text for the farmer (derja, arabizi)
 * @param data  raw module result for the app (charts, tables), or null
 * @param mock  true if the answer is not produced by a trained model yet
 */
public record ModuleAnswer(String reply, Object data, boolean mock) {

    public static ModuleAnswer stub(String reply) {
        return new ModuleAnswer(reply, null, true);
    }
}
