package tn.zitouna.ai.cropyield;

import tn.zitouna.ai.AiResult;

/** Response of M3 POST /predict. Parcel fields are null when no tree count is given. */
public record YieldResult(
        String governorate,
        int season,
        double regionalProductionTonnes,
        Double kgPerTree,
        Double parcelEstimateKg,
        Double parcelLowKg,
        Double parcelHighKg,
        String modelVersion,
        boolean mock) implements AiResult {
}
