package tn.zitouna.ai.trees;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

/** Final count after the farmer's review. corrected: boxes were removed or added by hand. */
public record SaveTreeCountRequest(
        @NotNull @PositiveOrZero Integer count,
        @PositiveOrZero Double densityPerHa,
        boolean densityEstimated,
        boolean corrected) {
}
