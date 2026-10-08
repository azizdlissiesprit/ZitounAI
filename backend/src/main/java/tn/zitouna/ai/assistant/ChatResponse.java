package tn.zitouna.ai.assistant;

import java.util.List;

import tn.zitouna.ai.AiResult;

/**
 * reply: text shown in the chat (derja, arabizi).
 * suggestions: intents to show as buttons when clarify is true (empty otherwise).
 * data: raw result of the module that answered (IrrigationResult, PriceResult...), or null.
 */
public record ChatResponse(
        String reply,
        Intent intent,
        boolean clarify,
        List<Intent> suggestions,
        Object data,
        boolean mock) implements AiResult {
}
