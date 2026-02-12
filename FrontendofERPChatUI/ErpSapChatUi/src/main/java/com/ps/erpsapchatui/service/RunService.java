package com.ps.erpsapchatui.service;

import com.ps.erpsapchatui.model.Run;
import com.ps.erpsapchatui.model.RunStatus;
import com.ps.erpsapchatui.store.RunStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.List;
import java.util.Map;

@Component
public class RunService {

    private final WebClient webClient;

    public RunService(@Value("${python.baseUrl}") String baseUrl) {
        this.webClient = WebClient.builder()
                .baseUrl(baseUrl)
                .build();
    }

    public void startRun(String runId, String issue) {
        Map<String, Object> payload = Map.of(
                "runId", runId,
                "issue", issue
        );

        // fire-and-forget (async)
        webClient.post()
                .uri("/run")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(payload)
                .retrieve()
                .bodyToMono(Void.class)
                .subscribe();
    }

    public WebClient getWebClient() {
        return webClient;
    }

}

