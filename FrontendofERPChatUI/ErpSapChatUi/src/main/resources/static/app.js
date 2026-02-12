// Global State
let runId = null;
let pollTimer = null;

// Initialize once DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("startBtn");
    const issueInput = document.getElementById("issueInput");
    const resetBtn = document.getElementById("resetBtn");

    if (startBtn) startBtn.addEventListener("click", startRun);
    if (issueInput) {
        issueInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") startRun();
        });
    }
    if (resetBtn) resetBtn.addEventListener("click", resetApp);
});

async function startRun() {
    const startBtn = document.getElementById("startBtn");
    const issueInput = document.getElementById("issueInput");
    const resultsCard = document.getElementById("resultsCard");
    const stepsList = document.getElementById("stepsList");

    const issue = issueInput.value.trim();
    if (!issue) {
        alert("Please describe the issue first.");
        return;
    }

    // Lock UI
    startBtn.disabled = true;
    startBtn.innerText = "Working...";
    resultsCard.classList.remove("hidden");
    stepsList.innerHTML = "";
    document.getElementById("resetBtn").classList.add("hidden");

    try {
        const res = await fetch("/runs", {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ issue })
        });

        const data = await res.json();
        if (data.error) throw new Error(data.error);

        runId = data.runId;
        document.getElementById("runIdDisplay").innerText = runId;
        updateStatusPill("RUNNING");
        document.getElementById("pollingIndicator").classList.remove("hidden");

        // Start Polling
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(loadSteps, 2000);
        await loadSteps();

    } catch (err) {
        showError(err.message || "Connection failed");
    }
}

async function loadSteps() {
    if (!runId) return;

    try {
        const [stepsRes, runRes] = await Promise.all([
            fetch(`/runs/${runId}/steps`),
            fetch(`/runs/${runId}`)
        ]);

        const steps = await stepsRes.json();
        const run = await runRes.json();

        renderSteps(steps);

        if (!run.error) {
            updateStatusPill(run.status);
            document.getElementById("stepCount").innerText = `Steps: ${run.stepsCount}`;

            if (run.status === "COMPLETED" || run.status === "FAILED") {
                stopPolling();
            }
        }
    } catch (err) {
        console.error("Polling error:", err);
    }
}

function renderSteps(steps) {
    const stepsList = document.getElementById("stepsList");
    stepsList.innerHTML = "";
    steps.forEach((step, index) => {
        const isLast = index === steps.length - 1;
        const div = document.createElement("div");
        div.className = "step-item";
        if (isLast) div.style.fontWeight = "600";

        div.innerHTML = `
            <div class="step-icon">${index + 1}</div>
            <div class="step-content">${step}</div>
        `;
        stepsList.appendChild(div);
    });
}

function updateStatusPill(status) {
    const pill = document.getElementById("statusPill");
    pill.innerText = status;
    pill.className = "pill";
    if (status === "COMPLETED") pill.classList.add("pill-completed");
    else if (status === "FAILED") pill.classList.add("pill-failed");
    else pill.classList.add("pill-running");
}

function stopPolling() {
    clearInterval(pollTimer);
    document.getElementById("startBtn").disabled = false;
    document.getElementById("startBtn").innerText = "Start Assistant";
    document.getElementById("pollingIndicator").classList.add("hidden");
    document.getElementById("resetBtn").classList.remove("hidden");
}

function showError(msg) {
    updateStatusPill("FAILED");
    document.getElementById("stepsList").innerHTML = `<div style="color:red; border:1px solid red; padding:10px; border-radius:4px;">${msg}</div>`;
    stopPolling();
}

function resetApp() {
    runId = null;
    document.getElementById("issueInput").value = "";
    document.getElementById("resultsCard").classList.add("hidden");
}