package com.ps.erpsapchatui.store;

import com.ps.erpsapchatui.model.Run;
import com.ps.erpsapchatui.model.RunStatus;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.Collection;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RunStore
{
    private final Map<String, Run> runs = new ConcurrentHashMap<>();

    public Run createRun(String issue)
    {
        String runId = "run-" + UUID.randomUUID().toString();
        Run run = new Run();
        run.setRunId(runId);
        run.setIssue(issue);
        run.setCreatedAt(Instant.now());
        run.setStatus(RunStatus.CREATED);
        runs.put(runId, run);
        return run;
    }

    public Run getRun(String runId)
    {
        return runs.get(runId);
    }

    public Collection<Run> getAllRuns()
    {
        return runs.values();
    }

    public void updateStatus(String runId, RunStatus status)
    {
        Run run =  runs.get(runId);
        if(run!=null)
        {
            run.setStatus(status);
        }
    }

    public void addStepIfnotExists(String runId, String step)
    {
        Run run = runs.get(runId);
        if(run!=null)
        {
            if(!run.getSteps().contains(step))
            {
                run.getSteps().add(step);
            }
        }
    }

}
