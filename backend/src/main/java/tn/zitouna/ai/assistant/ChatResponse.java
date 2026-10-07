package tn.zitouna.ai.assistant;

import java.util.List;

import tn.zitouna.ai.AiResult;

/** answeredBy: which module produced the answer (M5 for RAG, M2/M3/M4 when routed). */
public record ChatResponse(
        String intent,
        String answer,
        String answeredBy,
        List<AssistantResult.Source> sources,
        boolean mock) implements AiResult {
}
