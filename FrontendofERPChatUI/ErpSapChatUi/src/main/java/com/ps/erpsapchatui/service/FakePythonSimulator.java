package com.ps.erpsapchatui.service;

import com.ps.erpsapchatui.model.RunStatus;
import com.ps.erpsapchatui.store.RunStore;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class FakePythonSimulator {

    private final RunStore runStore;

    // track progress per run
    private final Map<String, Integer> progress = new ConcurrentHashMap<>();

    private static final List<String> FAKE_STEPS = List.of(
            "Received issue from user",
            "Opening SAP SuccessFactors",
            "Navigating to Admin Center",
            "Searching for Proxy Management",
            "Checking role-based permissions",
            "Identified missing permission: Proxy Admin",
            "Suggested fix: Grant permission and retry"
    );

    public FakePythonSimulator(RunStore runStore) {
        this.runStore = runStore;
    }

    public void advanceRun(String runId) {

        int current = progress.getOrDefault(runId, 0);

        if (current < FAKE_STEPS.size()) {
            runStore.addStepIfnotExists(runId, FAKE_STEPS.get(current));
            progress.put(runId, current + 1);
        } else {
            runStore.updateStatus(runId, RunStatus.COMPLETED);
        }
    }
}
