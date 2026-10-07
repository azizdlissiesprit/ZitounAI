package tn.zitouna.ai.assistant;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import tn.zitouna.ai.AiServiceClient;
import tn.zitouna.config.AiProperties;

/** M5 · Derja assistant (intent classification + RAG). */
@Component
public class AssistantClient extends AiServiceClient {

    public AssistantClient(RestClient.Builder builder, AiProperties props) {
        super("M5 assistant service", props.assistantUrl(), builder, props.timeout());
    }

    public AssistantResult ask(String message) {
        return postJson("/predict", new Request(message), AssistantResult.class);
    }

    public record Request(String message) {
    }
}
