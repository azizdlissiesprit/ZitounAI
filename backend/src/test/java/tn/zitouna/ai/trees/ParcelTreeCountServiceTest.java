package tn.zitouna.ai.trees;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;

import tn.zitouna.ai.AiServiceException;
import tn.zitouna.history.HistoryService;
import tn.zitouna.history.PredictionType;
import tn.zitouna.parcel.ParcelService;
import tn.zitouna.parcel.TreeCountSource;

@ExtendWith(MockitoExtension.class)
class ParcelTreeCountServiceTest {

    private static final MockMultipartFile IMAGE =
            new MockMultipartFile("image", "parcel.jpg", "image/jpeg", new byte[] { 1, 2, 3 });

    @Mock
    private TreeCountClient client;
    @Mock
    private ParcelService parcelService;
    @Mock
    private HistoryService historyService;
    @InjectMocks
    private ParcelTreeCountService service;

    private static TreeCountResult result(int count) {
        return new TreeCountResult(count, List.of(new TreeCountResult.Box(0, 10, 10, 40, 40, 0.9)), 1.0, List.of(),
                18.3, false, 7.76, 0.1, 21.5, new TreeCountResult.ImageSize(1024, 683), List.of(), "PNG...", 2350,
                "m6-yolo11n", false);
    }

    @Test
    void previewReturnsTheCountWithoutSavingIt() {
        var options = new TreeCountClient.Options("[[0,0],[100,0],[100,100]]", 0.1, null, null, false);
        when(client.count(IMAGE, options)).thenReturn(result(142));

        TreeCountResult res = service.preview(1L, 5L, IMAGE, options);

        assertThat(res.count()).isEqualTo(142);
        verify(parcelService).getOwned(1L, 5L); // ownership checked
        verify(parcelService, never()).saveTreeCount(anyLong(), anyLong(), anyInt(), any(), anyBoolean(), any());
        ArgumentCaptor<TreeCountResult> recorded = ArgumentCaptor.forClass(TreeCountResult.class);
        verify(historyService).record(eq(1L), eq(5L), eq(PredictionType.TREE_COUNT), any(), recorded.capture());
        assertThat(recorded.getValue().annotatedImage()).isNull(); // no heavy PNG in the history
    }

    @Test
    void timeoutOfM6IsAClearErrorAndNothingIsSaved() {
        when(client.count(any(), any()))
                .thenThrow(new AiServiceException(HttpStatus.GATEWAY_TIMEOUT, "M6 tree counting service did not answer in time"));

        assertThatThrownBy(() -> service.preview(1L, 5L, IMAGE, TreeCountClient.Options.NONE))
                .isInstanceOf(AiServiceException.class)
                .hasMessageContaining("did not answer in time")
                .extracting(e -> ((AiServiceException) e).getStatus()).isEqualTo(HttpStatus.GATEWAY_TIMEOUT);
        verify(parcelService, never()).saveTreeCount(anyLong(), anyLong(), anyInt(), any(), anyBoolean(), any());
    }

    @Test
    void correctedCountIsSavedAsCorrected() {
        service.save(1L, 5L, new SaveTreeCountRequest(140, 18.0, true, true));
        verify(parcelService).saveTreeCount(1L, 5L, 140, 18.0, true, TreeCountSource.CORRECTED);
    }

    @Test
    void uncorrectedCountIsSavedAsModel() {
        service.save(1L, 5L, new SaveTreeCountRequest(142, null, false, false));
        verify(parcelService).saveTreeCount(1L, 5L, 142, null, false, TreeCountSource.MODEL);
    }
}
