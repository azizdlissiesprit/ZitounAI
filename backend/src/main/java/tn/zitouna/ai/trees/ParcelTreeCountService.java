package tn.zitouna.ai.trees;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import lombok.RequiredArgsConstructor;
import tn.zitouna.history.HistoryService;
import tn.zitouna.history.PredictionType;
import tn.zitouna.parcel.ParcelDto;
import tn.zitouna.parcel.ParcelService;
import tn.zitouna.parcel.TreeCountSource;

/**
 * Counting the trees of a parcel in two steps: M6 detects (preview, nothing saved), the farmer reviews
 * and corrects the boxes in the app, then the final count is saved on the parcel (read by M3).
 */
@Service
@RequiredArgsConstructor
public class ParcelTreeCountService {

    private final TreeCountClient treeCountClient;
    private final ParcelService parcelService;
    private final HistoryService historyService;

    /** Calls M6 and returns its result WITHOUT saving it on the parcel. */
    public TreeCountResult preview(Long userId, Long parcelId, MultipartFile image, TreeCountClient.Options options) {
        parcelService.getOwned(userId, parcelId);
        TreeCountResult result = treeCountClient.count(image, options);
        Map<String, Object> request = new HashMap<>();
        request.put("fileName", String.valueOf(image.getOriginalFilename()));
        request.put("polygon", options.polygon() != null);
        request.put("gsdM", options.gsdM());
        request.put("areaHa", options.areaHa());
        request.put("zoom", options.zoom());
        historyService.record(userId, parcelId, PredictionType.TREE_COUNT, request, result.withoutImage());
        return result;
    }

    /** Saves the count the farmer validated (possibly corrected) on the parcel. */
    public ParcelDto save(Long userId, Long parcelId, SaveTreeCountRequest request) {
        return parcelService.saveTreeCount(userId, parcelId, request.count(), request.densityPerHa(),
                request.densityEstimated(), request.corrected() ? TreeCountSource.CORRECTED : TreeCountSource.MODEL);
    }
}
