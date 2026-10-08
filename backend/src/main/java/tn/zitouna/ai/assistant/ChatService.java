package tn.zitouna.ai.assistant;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import tn.zitouna.ai.AiServiceException;
import tn.zitouna.ai.assistant.modules.ChatContext;
import tn.zitouna.ai.assistant.modules.DiseaseService;
import tn.zitouna.ai.assistant.modules.IrrigationService;
import tn.zitouna.ai.assistant.modules.ModuleAnswer;
import tn.zitouna.ai.assistant.modules.PriceService;
import tn.zitouna.ai.assistant.modules.RagService;
import tn.zitouna.ai.assistant.modules.TreeCountService;
import tn.zitouna.ai.assistant.modules.WeatherService;
import tn.zitouna.ai.assistant.modules.YieldService;
import tn.zitouna.history.HistoryService;
import tn.zitouna.history.PredictionType;
import tn.zitouna.parcel.Parcel;
import tn.zitouna.parcel.ParcelService;

/**
 * Chat orchestration: M5 detects the intent, then the question is routed to the module that
 * can answer it. A module failure never breaks the chat: the farmer gets a "try again" reply.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChatService {

    static final String GREETING = "Aslema! Na3ref n3awnek fil mardh mta3 el zitoun, el sgi, el ta9s, el saba, "
            + "el soum w 3add el zitoun. Chnowa sou2alek?";
    static final String OFF_TOPIC = "Sameh7ni, ana n3awen ken fil fla7a mta3 el zitoun. "
            + "Jarreb mathalan: '9adech nesgi zitouni had el jem3a?'";
    static final String MODULE_DOWN = "Sameh7ni, ma najamtech nejawbek tawa. 3awed ba3d chwaya.";

    private final IntentClient intentClient;
    private final ParcelService parcelService;
    private final HistoryService historyService;
    private final DiseaseService diseaseService;
    private final IrrigationService irrigationService;
    private final WeatherService weatherService;
    private final YieldService yieldService;
    private final PriceService priceService;
    private final TreeCountService treeCountService;
    private final RagService ragService;

    public ChatResponse chat(Long userId, ChatRequest request) {
        Parcel parcel = request.parcelId() == null ? null : parcelService.getOwned(userId, request.parcelId());
        IntentResponse nlu = request.forcedIntent() != null
                ? IntentResponse.forced(request.forcedIntent())
                : intentClient.detect(request.text());

        ChatResponse response = nlu.clarify()
                ? new ChatResponse(nlu.question(), nlu.intent(), true, suggestions(nlu), null, nlu.mock())
                : route(nlu, new ChatContext(userId, request.text(), parcel, governorate(nlu)));

        historyService.record(userId, request.parcelId(), PredictionType.CHAT, request, response);
        return response;
    }

    private ChatResponse route(IntentResponse nlu, ChatContext ctx) {
        Intent intent = nlu.intent();
        try {
            ModuleAnswer module = switch (intent) {
                case MALADIE -> diseaseService.answer(ctx);
                case IRRIGATION -> irrigationService.answer(ctx);
                case METEO_ALERTE -> weatherService.answer(ctx);
                case RECOLTE -> yieldService.answer(ctx);
                case PRIX_VENTE -> priceService.answer(ctx);
                case COMPTAGE -> treeCountService.answer(ctx);
                case CONSEIL_GENERAL -> ragService.answer(ctx);
                case SALUTATION -> new ModuleAnswer(GREETING, null, false);
                case HORS_SUJET -> new ModuleAnswer(OFF_TOPIC, null, false);
            };
            return answer(intent, module.reply(), module.data(), nlu.mock() || module.mock());
        } catch (AiServiceException e) {
            log.warn("Module for intent {} failed: {}", intent, e.getMessage());
            return answer(intent, MODULE_DOWN, null, nlu.mock());
        }
    }

    private static ChatResponse answer(Intent intent, String reply, Object data, boolean mock) {
        return new ChatResponse(reply, intent, false, List.of(), data, mock);
    }

    /**
     * Candidate intents become buttons; greetings and off-topic make no sense as buttons.
     * With fewer than 2 left (e.g. the domain guard fired on "hors_sujet"), the main topics are added.
     */
    private static List<Intent> suggestions(IntentResponse nlu) {
        List<Intent> intents = nlu.candidates() == null ? List.of()
                : nlu.candidates().stream().map(IntentResponse.Candidate::intent).filter(Intent::isSuggestable).toList();
        if (intents.size() >= 2) {
            return intents;
        }
        Set<Intent> padded = new LinkedHashSet<>(intents);
        IntentResponse.fallback().candidates().forEach(c -> padded.add(c.intent()));
        return List.copyOf(padded);
    }

    private static String governorate(IntentResponse nlu) {
        return nlu.entities() == null ? null : nlu.entities().gouvernorat();
    }
}
