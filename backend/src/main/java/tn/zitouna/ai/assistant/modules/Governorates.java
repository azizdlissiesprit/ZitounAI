package tn.zitouna.ai.assistant.modules;

import java.util.Map;
import java.util.Optional;

/** Coordinates of each governorate's capital, keyed by the ids returned by M5 (entities.gouvernorat). */
final class Governorates {

    private static final Map<String, double[]> COORDINATES = Map.ofEntries(
            Map.entry("ariana", new double[] { 36.86, 10.19 }),
            Map.entry("beja", new double[] { 36.73, 9.18 }),
            Map.entry("ben arous", new double[] { 36.75, 10.22 }),
            Map.entry("bizerte", new double[] { 37.27, 9.87 }),
            Map.entry("gabes", new double[] { 33.88, 10.10 }),
            Map.entry("gafsa", new double[] { 34.42, 8.78 }),
            Map.entry("jendouba", new double[] { 36.50, 8.78 }),
            Map.entry("kairouan", new double[] { 35.68, 10.10 }),
            Map.entry("kasserine", new double[] { 35.17, 8.83 }),
            Map.entry("kebili", new double[] { 33.70, 8.97 }),
            Map.entry("kef", new double[] { 36.18, 8.71 }),
            Map.entry("mahdia", new double[] { 35.50, 11.06 }),
            Map.entry("manouba", new double[] { 36.81, 10.10 }),
            Map.entry("medenine", new double[] { 33.35, 10.50 }),
            Map.entry("monastir", new double[] { 35.78, 10.83 }),
            Map.entry("nabeul", new double[] { 36.45, 10.73 }),
            Map.entry("sfax", new double[] { 34.74, 10.76 }),
            Map.entry("sidi bouzid", new double[] { 35.04, 9.48 }),
            Map.entry("siliana", new double[] { 36.08, 9.37 }),
            Map.entry("sousse", new double[] { 35.83, 10.64 }),
            Map.entry("tataouine", new double[] { 32.93, 10.45 }),
            Map.entry("tozeur", new double[] { 33.92, 8.13 }),
            Map.entry("tunis", new double[] { 36.81, 10.18 }),
            Map.entry("zaghouan", new double[] { 36.40, 10.14 }));

    private Governorates() {
    }

    /** [latitude, longitude], or empty for an unknown / null id. */
    static Optional<double[]> coordinates(String governorate) {
        return governorate == null ? Optional.empty() : Optional.ofNullable(COORDINATES.get(governorate));
    }
}
