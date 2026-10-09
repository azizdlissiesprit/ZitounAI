package tn.zitouna.ai.assistant.modules;

import java.util.List;
import java.util.Locale;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import tn.zitouna.ai.cropyield.YieldClient;
import tn.zitouna.ai.cropyield.YieldResult;

/** recolte -> M3. Uses the existing M3 client (still in mock mode until M3's model is ready). */
@Service
@RequiredArgsConstructor
public class YieldChatService implements YieldService {

    private final YieldClient yieldClient;

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        var location = ctx.location().orElse(null);
        if (location == null) {
            return new ModuleAnswer(Replies.ASK_LOCATION, null, false);
        }
        Integer trees = ctx.parcel() != null ? ctx.parcel().getTreeCount() : null;
        YieldResult y = yieldClient.predict(
                new YieldClient.Request(location.governorate(), YieldClient.currentSeason(), trees));

        String reply = String.format(Locale.ROOT, "صابة %s (موسم %d/%d) ≈ %.0f طن زيتون.",
                Governorates.arabic(y.governorate()), y.season(), y.season() + 1, y.regionalProductionTonnes());
        reply += y.parcelEstimateKg() != null
                ? String.format(Locale.ROOT, " للقطعة « %s » (%d شجرة): ≈ %.0f كغ زيتون (بين %.0f و %.0f).",
                        location.label(), trees, y.parcelEstimateKg(), y.parcelLowKg(), y.parcelHighKg())
                : " اختار قطعة فيها عدد الزيتون باش نحسبلك صابتك.";
        Fact fact = Fact.of("M3", y.mock(),
                "gouvernorat", y.governorate(),
                "saison", y.season() + "/" + (y.season() + 1),
                "production_regionale_tonnes", Math.round(y.regionalProductionTonnes()),
                "nombre_arbres", trees,
                "kg_olives_par_arbre", y.kgPerTree(),
                "estimation_parcelle_kg_olives", y.parcelEstimateKg(),
                "fourchette_parcelle_kg", y.parcelEstimateKg() == null ? null : y.parcelLowKg() + " - " + y.parcelHighKg());
        return new ModuleAnswer(reply, y, y.mock(), List.of(fact));
    }
}
