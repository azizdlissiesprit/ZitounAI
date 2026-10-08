package tn.zitouna.ai.assistant.modules;

import java.util.Locale;

import org.springframework.stereotype.Service;

import lombok.RequiredArgsConstructor;
import tn.zitouna.ai.price.PriceClient;
import tn.zitouna.ai.price.PriceResult;

/** prix_vente -> M4. Uses the existing M4 client (still in mock mode until M4's model is ready). */
@Service
@RequiredArgsConstructor
public class PriceChatService implements PriceService {

    private final PriceClient priceClient;

    @Override
    public ModuleAnswer answer(ChatContext ctx) {
        PriceResult price = priceClient.predict(new PriceClient.Request(8, null));
        double today = price.history().isEmpty() ? 0 : price.history().getLast().price();
        String advice = PriceResult.SELL_NOW.equals(price.recommendation())
                ? "Na9tara7 tbi3 taw."
                : "Na9tara7 tkhazzen zitek w testanna chwaya.";
        String reply = String.format(Locale.ROOT, "%s Soum el youm ≈ %.2f %s/%s. %s",
                advice, today, price.currency(), price.unit(), price.reason());
        return new ModuleAnswer(reply, price, price.mock());
    }
}
