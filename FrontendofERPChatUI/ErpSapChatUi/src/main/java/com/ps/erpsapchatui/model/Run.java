package com.ps.erpsapchatui.model;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data

public class Run
{
    private String runId;
    private String issue;
    private Instant createdAt;
    private RunStatus status;
    private List<String> steps = new ArrayList<>();
}
