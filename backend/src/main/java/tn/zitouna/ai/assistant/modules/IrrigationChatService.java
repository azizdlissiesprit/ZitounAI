package tn.zitouna.ai.assistant.modules;

import java.util.Locale;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import tn.zitouna.ai.irrigation.IrrigationClient;
import tn.zitouna.ai.irrigation.IrrigationResult;

/** irrigation -> M2. Uses the existing M2 client (still in mock mode until M2's model is ready). */
@Service
@RequiredArgsConstructor
public class IrrigationChatService implements IrrigationService {

    private final IrrigationClient irrigationClient;

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        var location = ctx.location().orElse(null);
        if (location == null) {
            return new ModuleAnswer(Replies.ASK_LOCATION, null, false);
        }
        Integer trees = ctx.parcel() != null ? ctx.parcel().getTreeCount() : null;
        Double area = ctx.parcel() != null ? ctx.parcel().getAreaHa() : null;
        IrrigationResult plan = irrigationClient.predict(new IrrigationClient.Request(
                location.latitude(), location.longitude(), trees, area, 7));

        long days = plan.days().stream().filter(IrrigationResult.Day::irrigate).count();
        double totalMm = plan.days().stream().mapToDouble(IrrigationResult.Day::waterNeedMm).sum();
        Double liters = plan.days().stream().filter(IrrigationResult.Day::irrigate)
                .map(IrrigationResult.Day::litersPerTree).filter(l -> l != null).findFirst().orElse(null);

        String reply = days == 0
                ? "Fi %s ma tesga7ech tesgi el 7 ayyem ejjeyin.".formatted(location.label())
                : String.format(Locale.ROOT, "Fi %s, el 7 ayyem ejjeyin: lazmek tesgi %d marrat, el 7aja el kol ≈ %.0f mm%s.",
                        location.label(), days, totalMm,
                        liters == null ? "" : String.format(Locale.ROOT, " (≈ %.0f litre lel chajra fil marra)", liters));
        return new ModuleAnswer(reply, plan, plan.mock());
    }
}
