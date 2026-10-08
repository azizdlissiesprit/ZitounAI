package tn.zitouna.ai.assistant.modules;

import java.util.stream.Collectors;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import tn.zitouna.ai.irrigation.IrrigationClient;
import tn.zitouna.ai.irrigation.IrrigationResult;

/** meteo_alerte -> M2 alerts. Uses the existing M2 client (still in mock mode until M2's model is ready). */
@Service
@RequiredArgsConstructor
public class WeatherChatService implements WeatherService {

    private final IrrigationClient irrigationClient;

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        var location = ctx.location().orElse(null);
        if (location == null) {
            return new ModuleAnswer(Replies.ASK_LOCATION, null, false);
        }
        IrrigationResult result = irrigationClient.predict(new IrrigationClient.Request(
                location.latitude(), location.longitude(), null, null, 7));

        String reply = result.alerts().isEmpty()
                ? "Ma fama 7atta tanbih (jlid walla skhana) fi %s el 7 ayyem ejjeyin.".formatted(location.label())
                : "Rod belek fi %s: %s".formatted(location.label(), result.alerts().stream()
                        .map(a -> a.date() + " — " + a.message())
                        .collect(Collectors.joining(" ")));
        return new ModuleAnswer(reply, result.alerts(), result.mock());
    }
}
