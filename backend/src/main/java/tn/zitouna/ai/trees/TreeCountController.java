package tn.zitouna.ai.trees;

import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import tn.zitouna.auth.CurrentUser;
import tn.zitouna.parcel.ParcelDto;

@RestController
@RequestMapping("/api/parcels/{parcelId}/tree-count")
@RequiredArgsConstructor
public class TreeCountController {

    private final ParcelTreeCountService service;

    /** Step 1: M6 counts the trees on the image. Nothing is saved: the farmer reviews the boxes first. */
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public TreeCountResult count(@AuthenticationPrincipal Jwt jwt, @PathVariable Long parcelId,
            @RequestPart("image") MultipartFile image,
            @RequestParam(required = false) String polygon,
            @RequestParam(required = false) Double gsdM,
            @RequestParam(required = false) Double areaHa,
            @RequestParam(required = false) Double zoom,
            @RequestParam(defaultValue = "false") boolean annotated) {
        var options = new TreeCountClient.Options(polygon, gsdM, areaHa, zoom, annotated);
        return service.preview(CurrentUser.id(jwt), parcelId, image, options);
    }

    /** Step 2: saves the final (possibly corrected) count on the parcel. */
    @PutMapping
    public ParcelDto save(@AuthenticationPrincipal Jwt jwt, @PathVariable Long parcelId,
            @Valid @RequestBody SaveTreeCountRequest request) {
        return service.save(CurrentUser.id(jwt), parcelId, request);
    }
}
