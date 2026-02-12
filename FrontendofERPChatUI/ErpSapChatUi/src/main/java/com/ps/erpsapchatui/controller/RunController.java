package com.ps.erpsapchatui.controller;

import com.ps.erpsapchatui.model.Run;
import com.ps.erpsapchatui.model.RunStatus;
import com.ps.erpsapchatui.service.RunService;
import com.ps.erpsapchatui.store.RunStore;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
public class RunController {

    private final RunStore runStore;
    private final RunService pythonClient;

    public RunController(RunStore runStore, RunService pythonClient) {
        this.runStore = runStore;
        this.pythonClient = pythonClient;
    }

    @PostMapping("/runs")
    public Map<String, Object> startRun(@RequestBody Map<String, String> body) {
        String issue = body.getOrDefault("issue", "").trim();
        if (issue.isEmpty()) {
            return Map.of("error", "Issue is required");
        }

        Run run = runStore.createRun(issue);
        runStore.updateStatus(run.getRunId(), RunStatus.RUNNING);

        pythonClient.startRun(run.getRunId(), issue);

        return Map.of(
                "runId", run.getRunId(),
                "status", run.getStatus().name()
        );
    }

    @GetMapping("/runs/{runId}")
    public Map<String, Object> getRun(@PathVariable String runId) {
        Run run = runStore.getRun(runId);
        if (run == null) return Map.of("error", "Run not found");
        return Map.of(
                "runId", run.getRunId(),
                "issue", run.getIssue(),
                "status", run.getStatus().name(),
                "stepsCount", run.getSteps().size()
        );
    }

    @GetMapping("/runs/{runId}/steps")
    public List<String> getSteps(@PathVariable String runId) {
        Run run = runStore.getRun(runId);
        if (run == null) return List.of("Run not found");
        return run.getSteps();
    }
}