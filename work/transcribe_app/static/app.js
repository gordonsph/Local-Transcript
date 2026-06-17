const form = document.getElementById("uploadForm");
const audioInput = document.getElementById("audio");
const fileName = document.getElementById("fileName");
const dropzone = document.getElementById("dropzone");
const startButton = document.getElementById("startButton");
const jobPanel = document.getElementById("jobPanel");
const jobTitle = document.getElementById("jobTitle");
const jobMeta = document.getElementById("jobMeta");
const log = document.getElementById("log");
const downloads = document.getElementById("downloads");
const spinner = document.getElementById("spinner");
const barFill = document.getElementById("barFill");
const systemStatus = document.getElementById("systemStatus");
const savedPath = document.getElementById("savedPath");
const percentDone = document.getElementById("percentDone");
const eta = document.getElementById("eta");
const elapsed = document.getElementById("elapsed");
const pauseButton = document.getElementById("pauseButton");
const resumeButton = document.getElementById("resumeButton");
const terminateButton = document.getElementById("terminateButton");
const cpuUsage = document.getElementById("cpuUsage");
const ramUsage = document.getElementById("ramUsage");
const loadUsage = document.getElementById("loadUsage");
const gpuUsage = document.getElementById("gpuUsage");

let pollTimer = null;
let currentJobId = null;

function setFileLabel() {
  const file = audioInput.files[0];
  fileName.textContent = file ? file.name : "Choose audio";
}

function setBusy(isBusy) {
  startButton.disabled = isBusy;
  startButton.textContent = isBusy ? "Running..." : "Start transcript";
}

function progressFromMessage(message) {
  const match = /(\d+)%/.exec(message || "");
  return match ? Math.max(8, Math.min(100, Number(match[1]))) : 8;
}

function updateControlState(job) {
  const isRunning = job.status === "running";
  const isPaused = job.status === "paused";
  const hasProcess = Boolean(job.process_pid);
  pauseButton.disabled = !isRunning || !hasProcess;
  resumeButton.disabled = !isPaused || !hasProcess;
  terminateButton.disabled = !hasProcess || ["cancelling", "cancelled", "done", "failed"].includes(job.status);
}

function renderSystem(job) {
  const system = job.system || {};
  const process = system.process || {};
  const memory = system.memory || {};
  const load = system.load || {};
  cpuUsage.textContent = process.cpu_percent != null ? `${process.cpu_percent.toFixed(0)}% process` : "Waiting";
  ramUsage.textContent = process.rss_mb != null ? `${process.rss_mb} MB · ${memory.free_mb || "?"} MB free` : "Waiting";
  loadUsage.textContent = load["1m"] != null ? `${load["1m"]} / ${system.cpu_count || "?"} cores` : "Waiting";
  gpuUsage.textContent = "Metal active";
}

function renderJob(job) {
  jobPanel.hidden = false;
  jobTitle.textContent = job.message || job.status;
  jobMeta.textContent = `${job.language_label} · ${job.output_format_label}`;
  savedPath.textContent = job.output_location ? `Saved to ${job.output_location}` : "";
  const progress = Number(job.progress || 0);
  percentDone.textContent = `${progress.toFixed(0)}%`;
  eta.textContent = job.eta_label || (job.status === "done" ? "0s" : "Calculating");
  elapsed.textContent = job.elapsed_label || "0s";
  log.textContent = (job.log || []).join("\n");
  log.scrollTop = log.scrollHeight;
  const fillRatio = Math.max(0.02, Math.min(1, (progress || progressFromMessage(job.message)) / 100));
  barFill.style.transform = `scaleX(${fillRatio})`;
  updateControlState(job);
  renderSystem(job);

  downloads.innerHTML = "";
  if (job.files) {
    for (const [label, filename] of Object.entries(job.files)) {
      const link = document.createElement("a");
      link.href = `/download/${job.id}/${encodeURIComponent(filename)}`;
      link.textContent = label;
      downloads.appendChild(link);
    }
  }

  if (job.status === "done") {
    setBusy(false);
    spinner.classList.add("done");
    barFill.style.transform = "scaleX(1)";
    systemStatus.textContent = "Ready";
    clearInterval(pollTimer);
  } else if (job.status === "failed" || job.status === "cancelled") {
    setBusy(false);
    spinner.classList.add("done");
    jobTitle.innerHTML = `<span class="error">${job.error || job.message || "Stopped"}</span>`;
    systemStatus.textContent = "Ready";
    clearInterval(pollTimer);
  } else if (job.status === "paused") {
    spinner.classList.add("done");
    systemStatus.textContent = "Paused";
  } else {
    spinner.classList.remove("done");
  }
}

async function pollJob(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);
  const job = await response.json();
  renderJob(job);
}

async function controlJob(action) {
  if (!currentJobId) return;
  const response = await fetch(`/api/jobs/${currentJobId}/${action}`, { method: "POST" });
  const job = await response.json();
  renderJob(job);
}

audioInput.addEventListener("change", setFileLabel);

for (const eventName of ["dragenter", "dragover"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
  });
}

dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  audioInput.files = transfer.files;
  setFileLabel();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!audioInput.files[0]) return;

  setBusy(true);
  spinner.classList.remove("done");
  downloads.innerHTML = "";
  log.textContent = "";
  systemStatus.textContent = "Busy";
  jobPanel.hidden = false;
  jobTitle.textContent = "Uploading";
  jobMeta.textContent = "Preparing";
  barFill.style.transform = "scaleX(0.08)";

  const body = new FormData(form);
  const response = await fetch("/api/jobs", { method: "POST", body });
  const job = await response.json();
  if (!response.ok) {
    renderJob({ status: "failed", error: job.error || "Upload failed", log: [], files: {} });
    return;
  }

  renderJob(job);
  currentJobId = job.id;
  clearInterval(pollTimer);
  pollTimer = setInterval(() => pollJob(job.id), 2500);
});

pauseButton.addEventListener("click", () => controlJob("pause"));
resumeButton.addEventListener("click", () => controlJob("resume"));
terminateButton.addEventListener("click", () => controlJob("terminate"));
