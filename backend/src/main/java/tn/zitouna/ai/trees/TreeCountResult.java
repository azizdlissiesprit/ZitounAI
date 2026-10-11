package tn.zitouna.ai.trees;

import java.util.List;

import tn.zitouna.ai.AiResult;

/**
 * Response of M6 POST /count-trees. Boxes are in pixels of the uploaded image.
 * densityEstimated: true when no scale was given (density from an assumed 5 m crown).
 * annotatedImage: PNG in base64, only when requested (the app draws the boxes itself).
 */
public record TreeCountResult(
        int count,
        List<Box> boxes,
        Double zoomUsed,
        List<ZoomTrial> zoomTrials,
        Double densityPerHa,
        boolean densityEstimated,
        Double areaHa,
        Double gsdM,
        Double meanCrownM2,
        ImageSize imageSize,
        List<String> warnings,
        String annotatedImage,
        long processingMs,
        String modelVersion,
        boolean mock) implements AiResult {

    public record Box(int id, double x1, double y1, double x2, double y2, double score) {
    }

    public record ZoomTrial(double zoom, int n, double score, double crownPx) {
    }

    public record ImageSize(int width, int height) {
    }

    /** Same result without the (heavy) annotated image, for the history. */
    public TreeCountResult withoutImage() {
        return new TreeCountResult(count, boxes, zoomUsed, zoomTrials, densityPerHa, densityEstimated, areaHa, gsdM,
                meanCrownM2, imageSize, warnings, null, processingMs, modelVersion, mock);
    }
}
