package tn.zitouna.ai.trees;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

import tn.zitouna.ai.AiServiceClient;
import tn.zitouna.config.AiProperties;

/**
 * M6 · Olive tree counting (YOLO by tiles with automatic zoom). Long timeout: on CPU the automatic
 * zoom tries several scales and can take tens of seconds on a big image.
 */
@Component
public class TreeCountClient extends AiServiceClient {

    public TreeCountClient(RestClient.Builder builder, AiProperties props,
            @Value("${app.ai.trees-timeout:PT60S}") Duration timeout) {
        super("M6 tree counting service", props.treesUrl(), builder, timeout);
    }

    public TreeCountResult count(MultipartFile parcelImage, Options options) {
        Map<String, Object> fields = new HashMap<>();
        fields.put("polygon", options.polygon());
        fields.put("gsdM", options.gsdM());
        fields.put("areaHa", options.areaHa());
        fields.put("zoom", options.zoom());
        fields.put("annotated", options.annotated());
        return postImage("/count-trees", parcelImage, fields, TreeCountResult.class);
    }

    /**
     * @param polygon   parcel outline, JSON "[[x, y], ...]" in image pixels, or null for the whole image
     * @param gsdM      meters per pixel of the image, or null
     * @param areaHa    parcel area when gsdM is unknown, or null
     * @param zoom      forces one zoom instead of the automatic one, or null
     * @param annotated also return a PNG with the boxes drawn
     */
    public record Options(String polygon, Double gsdM, Double areaHa, Double zoom, boolean annotated) {
        public static final Options NONE = new Options(null, null, null, null, false);
    }
}
