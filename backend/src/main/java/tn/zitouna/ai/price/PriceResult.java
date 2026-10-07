package tn.zitouna.ai.price;

import java.time.LocalDate;
import java.util.List;

import tn.zitouna.ai.AiResult;

/** Response of M4 POST /predict. Prices are producer prices of olive oil in TND/kg. */
public record PriceResult(
        String currency,
        String unit,
        List<Point> history,
        List<Point> forecast,
        String recommendation,
        String reason,
        Double expectedGainTnd,
        String modelVersion,
        boolean mock) implements AiResult {

    public static final String SELL_NOW = "SELL_NOW";
    public static final String STORE = "STORE";

    /** low/high: prediction interval, null for historical points. */
    public record Point(LocalDate date, double price, Double low, Double high) {
    }
}
