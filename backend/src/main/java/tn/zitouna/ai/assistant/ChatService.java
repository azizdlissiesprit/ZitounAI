package tn.zitouna.ai.assistant;

import java.util.List;
import java.util.Locale;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import tn.zitouna.ai.AiServiceException;
import tn.zitouna.ai.cropyield.YieldClient;
import tn.zitouna.ai.cropyield.YieldResult;
import tn.zitouna.ai.irrigation.IrrigationClient;
import tn.zitouna.ai.irrigation.IrrigationResult;
import tn.zitouna.ai.price.PriceClient;
import tn.zitouna.ai.price.PriceResult;
import tn.zitouna.history.HistoryService;
import tn.zitouna.history.PredictionType;
import tn.zitouna.parcel.Parcel;
import tn.zitouna.parcel.ParcelService;

/**
 * Orchestration for the assistant: M5 detects the intent, then the backend routes the
 * question to the module that can answer it (M2, M3, M4). If that module fails, we fall
 * back to the RAG answer from M5 so the chat never breaks.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChatService {

    private static final String FALLBACK = "Je n'ai pas de réponse précise pour le moment. Reformulez votre question.";

    private final AssistantClient assistantClient;
    private final IrrigationClient irrigationClient;
    private final YieldClient yieldClient;
    private final PriceClient priceClient;
    private final ParcelService parcelService;
    private final HistoryService historyService;

    public ChatResponse chat(Long userId, ChatRequest request) {
        Parcel parcel = request.parcelId() == null ? null : parcelService.getOwned(userId, request.parcelId());
        AssistantResult nlu = assistantClient.ask(request.message());

        ChatResponse response;
        try {
            response = switch (nlu.intent()) {
                case "price" -> answerPrice(nlu);
                case "irrigation" -> parcel != null ? answerIrrigation(nlu, parcel) : rag(nlu);
                case "yield" -> parcel != null ? answerYield(nlu, parcel) : rag(nlu);
                case "disease" -> new ChatResponse(nlu.intent(),
                        "Prenez une photo de la feuille dans l'onglet « Diagnostic » pour identifier la maladie.",
                        "M1", nlu.sources(), nlu.mock());
                default -> rag(nlu);
            };
        } catch (AiServiceException e) {
            log.warn("Routing intent '{}' failed, falling back to RAG answer: {}", nlu.intent(), e.getMessage());
            response = rag(nlu);
        }

        historyService.record(userId, request.parcelId(), PredictionType.CHAT, request, response);
        return response;
    }

    private ChatResponse rag(AssistantResult nlu) {
        String answer = nlu.answer() != null ? nlu.answer() : FALLBACK;
        return new ChatResponse(nlu.intent(), answer, "M5", nlu.sources(), nlu.mock());
    }

    private ChatResponse answerPrice(AssistantResult nlu) {
        PriceResult price = priceClient.predict(new PriceClient.Request(8, null));
        String advice = PriceResult.SELL_NOW.equals(price.recommendation()) ? "vendre maintenant" : "stocker et attendre";
        String answer = "Conseil : %s. %s".formatted(advice, price.reason());
        return new ChatResponse(nlu.intent(), answer, "M4", List.of(), nlu.mock() || price.mock());
    }

    private ChatResponse answerIrrigation(AssistantResult nlu, Parcel parcel) {
        IrrigationResult plan = irrigationClient.predict(new IrrigationClient.Request(
                parcel.getLatitude(), parcel.getLongitude(), parcel.getTreeCount(), parcel.getAreaHa(), 7));
        long irrigationDays = plan.days().stream().filter(IrrigationResult.Day::irrigate).count();
        double totalMm = plan.days().stream().mapToDouble(IrrigationResult.Day::waterNeedMm).sum();
        String answer = String.format(Locale.FRANCE,
                "Pour « %s » : %d jour(s) d'irrigation conseillé(s) cette semaine, besoin total ≈ %.1f mm.%s",
                parcel.getName(), irrigationDays, totalMm,
                plan.alerts().isEmpty() ? "" : " Attention : " + plan.alerts().getFirst().message());
        return new ChatResponse(nlu.intent(), answer, "M2", List.of(), nlu.mock() || plan.mock());
    }

    private ChatResponse answerYield(AssistantResult nlu, Parcel parcel) {
        YieldResult y = yieldClient.predict(new YieldClient.Request(
                parcel.getGovernorate(), YieldClient.currentSeason(), parcel.getTreeCount()));
        String answer = y.parcelEstimateKg() != null
                ? String.format(Locale.FRANCE, "Récolte estimée pour « %s » : environ %.0f kg d'olives cette saison.",
                        parcel.getName(), y.parcelEstimateKg())
                : String.format(Locale.FRANCE,
                        "Production estimée à %s : %.0f tonnes. Indiquez le nombre d'arbres pour une estimation de votre parcelle.",
                        y.governorate(), y.regionalProductionTonnes());
        return new ChatResponse(nlu.intent(), answer, "M3", List.of(), nlu.mock() || y.mock());
    }
}
