package tn.zitouna.ai.trees;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.Executors;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.client.RestClient;

import com.sun.net.httpserver.HttpServer;

import tn.zitouna.ai.AiServiceException;
import tn.zitouna.config.AiProperties;

/** TreeCountClient against a real local HTTP server: multipart fields, parsing, timeout. */
class TreeCountClientTest {

    private static final String OK_JSON = """
            {"count":2,"boxes":[{"id":0,"x1":120.5,"y1":88.0,"x2":154.2,"y2":119.7,"score":0.91},
                                {"id":1,"x1":200.0,"y1":90.0,"x2":230.0,"y2":121.0,"score":0.88}],
             "zoomUsed":2.0,"zoomTrials":[{"zoom":1.0,"n":1,"score":0.61,"crownPx":18.0}],
             "densityPerHa":18.3,"densityEstimated":false,"areaHa":7.76,"gsdM":0.1,"meanCrownM2":21.5,
             "imageSize":{"width":1024,"height":683},"warnings":[],"annotatedImage":null,"processingMs":2350,
             "modelVersion":"m6-yolo11n","mock":false}""";

    private static final MockMultipartFile IMAGE =
            new MockMultipartFile("image", "parcel.png", "image/png", new byte[] { (byte) 0x89, 'P', 'N', 'G' });

    private HttpServer server;
    private volatile String receivedBody;

    @AfterEach
    void stop() {
        if (server != null) {
            server.stop(0);
        }
    }

    private TreeCountClient clientFor(long delayMs, Duration timeout) throws IOException {
        server = HttpServer.create(new InetSocketAddress("localhost", 0), 0);
        server.setExecutor(Executors.newCachedThreadPool());
        server.createContext("/count-trees", exchange -> {
            receivedBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.ISO_8859_1);
            try {
                Thread.sleep(delayMs);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            byte[] bytes = OK_JSON.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, bytes.length);
            exchange.getResponseBody().write(bytes);
            exchange.close();
        });
        server.start();
        String url = "http://localhost:" + server.getAddress().getPort();
        AiProperties props = new AiProperties(Duration.ofSeconds(30), null, null, null, null, null, url);
        return new TreeCountClient(RestClient.builder(), props, timeout);
    }

    @Test
    void sendsImageAndOptionsAsMultipartAndParsesTheResult() throws IOException {
        TreeCountClient client = clientFor(0, Duration.ofSeconds(5));
        var options = new TreeCountClient.Options("[[0,0],[100,0],[100,100]]", 0.1, null, 2.0, false);

        TreeCountResult res = client.count(IMAGE, options);

        assertThat(res.count()).isEqualTo(2);
        assertThat(res.boxes()).hasSize(2);
        assertThat(res.boxes().getFirst().x1()).isEqualTo(120.5);
        assertThat(res.zoomTrials().getFirst().crownPx()).isEqualTo(18.0);
        assertThat(res.imageSize().width()).isEqualTo(1024);
        assertThat(receivedBody)
                .contains("name=\"image\"", "name=\"polygon\"", "[[0,0],[100,0],[100,100]]", "name=\"gsdM\"",
                        "name=\"zoom\"", "name=\"annotated\"")
                .doesNotContain("name=\"areaHa\""); // null options are not sent
    }

    @Test
    void timeoutBecomesAClear504() throws IOException {
        TreeCountClient client = clientFor(1500, Duration.ofMillis(300));

        assertThatThrownBy(() -> client.count(IMAGE, TreeCountClient.Options.NONE))
                .isInstanceOf(AiServiceException.class)
                .hasMessageContaining("did not answer in time")
                .extracting(e -> ((AiServiceException) e).getStatus()).isEqualTo(HttpStatus.GATEWAY_TIMEOUT);
    }
}
