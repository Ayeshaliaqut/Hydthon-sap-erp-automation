package com.ps.erpsapchatui.service;

import com.ps.erpsapchatui.model.Run;
import com.ps.erpsapchatui.model.RunStatus;

import com.ps.erpsapchatui.store.RunStore;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public  class PythonPollingService {

    private final RunStore runStore;
    private final RunService pythonClient;
    private final FakePythonSimulator fakePythonSimulator;

    @Value("${python.enabled:false}")
    private boolean pythonEnabled;

    public PythonPollingService(RunStore runStore, RunService pythonClient, FakePythonSimulator fakePythonSimulator) {
        this.runStore = runStore;
        this.pythonClient = pythonClient;
        this.fakePythonSimulator = fakePythonSimulator;
    }

    public static class PythonStatusResponse {
        public String status;
        public List<String> steps;
        public boolean done;
        public String error;
    }

    @Scheduled(fixedDelayString = "${polling.intervalMs:2000}")
    public void pollPython() {
        for (Run run : runStore.getAllRuns()) {
            if (run.getStatus() != RunStatus.RUNNING) continue;

            //Go to Application and you can toggle python.enabled to false or true
            //for now it is false for demo purposes
            if(!pythonEnabled)
            {
                fakePythonSimulator.advanceRun(run.getRunId());
            }




            pythonClient.getWebClient().get()
                    .uri("/runs/{runId}/status", run.getRunId())
                    .retrieve()
                    .bodyToMono(PythonStatusResponse.class)
                    .subscribe(resp -> {
                        if (resp.steps != null) {
                            for (String s : resp.steps) {
                                runStore.addStepIfnotExists(run.getRunId(), s);
                            }
                        }
                        if (resp.done) {
                            runStore.updateStatus(run.getRunId(), RunStatus.COMPLETED);
                        }
                        if (resp.error != null && !resp.error.isBlank()) {
                            runStore.updateStatus(run.getRunId(), RunStatus.FAILED);
                            runStore.addStepIfnotExists(run.getRunId(), "ERROR: " + resp.error);
                        }
                    }, err -> {
                        // If python is down temporarily, don't crash; just log a step once.
                        runStore.addStepIfnotExists(run.getRunId(), "Waiting for Python agent...");
                    });
        }
    }
}
