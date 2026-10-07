package tn.zitouna.ai.assistant;

import java.util.List;

import tn.zitouna.ai.AiResult;

/**
 * Response of M5 POST /predict. intent: disease | irrigation | yield | price | general.
 * answer is the RAG answer (may be null when the intent is meant to be served by another module).
 */
public record AssistantResult(
        String intent,
        double confidence,
        String answer,
        List<Source> sources,
        String modelVersion,
        boolean mock) implements AiResult {

    public record Source(String title, String url) {
    }
}
