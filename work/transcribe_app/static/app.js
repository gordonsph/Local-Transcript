const form = document.getElementById("uploadForm");
const sourceType = document.getElementById("sourceType");
const sourceButtons = Array.from(document.querySelectorAll(".source-tab"));
const sourcePanels = Array.from(document.querySelectorAll(".source-panel"));
const audioInput = document.getElementById("audio");
const sourceUrl = document.getElementById("sourceUrl");
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
const statusPill = document.getElementById("statusPill");
const tbStatus = document.getElementById("tbStatus");
const tbStatusText = document.getElementById("tbStatusText");

// Update the global status text AND the colored dot (green=ready, amber=busy/
// paused/pending, red=error) so the indicator never lies about app state.
// Both indicators — the sidebar pill and the toolbar badge — move together.
function setStatus(text, state) {
  systemStatus.textContent = text;
  if (statusPill && state) statusPill.dataset.state = state;
  if (tbStatusText) tbStatusText.textContent = text;
  if (tbStatus && state) tbStatus.dataset.state = state;
}
const savedPath = document.getElementById("savedPath");
const sourcePath = document.getElementById("sourcePath");
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
const recordButton = document.getElementById("recordButton");
const stopRecordButton = document.getElementById("stopRecordButton");
const recordingTimer = document.getElementById("recordingTimer");
const recordingStatus = document.getElementById("recordingStatus");
const recordingTitle = document.getElementById("recordingTitle");
const liveWaveform = document.getElementById("liveWaveform");
const installButton = document.getElementById("installButton");
const installDialog = document.getElementById("installDialog");
const browserInstallButton = document.getElementById("browserInstallButton");

let pollTimer = null;
let currentJobId = null;
let currentSource = "file";
let isSubmitting = false;
let mediaRecorder = null;
let mediaStream = null;
let recordedBlob = null;
let recordedName = "";
let recordedChunks = [];
let recordingStartedAt = 0;
let recordingTimerId = null;
let deferredInstallPrompt = null;
let pollFailures = 0;
let modelReady = !startButton.disabled;
let setupPollTimer = null;

function setFileLabel() {
  const file = audioInput.files[0];
  fileName.textContent = file ? file.name : "Choose audio";
  updatePrimaryAction();
}

function setBusy(isBusy) {
  isSubmitting = isBusy;
  updatePrimaryAction();
}

function formatClock(seconds) {
  seconds = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
}

function activeSourceLabel() {
  if (currentSource === "url") return "Import URL";
  if (currentSource === "live") return recordedBlob ? "Save & transcribe recording" : "Record first";
  return "Start transcript";
}

function sourceReady() {
  if (currentSource === "file") return Boolean(audioInput.files[0]);
  if (currentSource === "url") return Boolean(sourceUrl.value.trim());
  return Boolean(recordedBlob);
}

function updatePrimaryAction() {
  startButton.textContent = isSubmitting ? "Running..." : activeSourceLabel();
  startButton.disabled = isSubmitting || !modelReady || !sourceReady();
  sourceButtons.forEach((button) => {
    button.disabled = isSubmitting;
  });
  // Lock the job settings while a transcription is running so they visibly can't
  // be edited mid-run (they only apply at submit time anyway).
  for (const id of ["language", "format", "outputLocation", "terminology", "sourceUrl"]) {
    const el = document.getElementById(id);
    if (el) el.disabled = isSubmitting;
  }
  if (recordButton) {
    recordButton.disabled = isSubmitting || Boolean(mediaRecorder);
  }
  if (stopRecordButton) {
    stopRecordButton.disabled = !mediaRecorder;
  }
}

function switchSource(nextSource) {
  // Never leave the mic live behind a hidden panel: if the user is recording on
  // the Live tab and switches away, stop the recorder (and release the stream)
  // first — otherwise the stop control disappears and the mic stays hot.
  if (nextSource !== "live" && (mediaRecorder || mediaStream)) {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();  // 'stop' handler clears mediaRecorder + stream
    } else {
      stopMediaStream();
    }
  }
  currentSource = nextSource;
  sourceType.value = nextSource;
  sourceButtons.forEach((button) => {
    const active = button.dataset.source === nextSource;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  sourcePanels.forEach((panel) => {
    panel.hidden = panel.dataset.panel !== nextSource;
  });
  updatePrimaryAction();
}

function recordingMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((type) => window.MediaRecorder && MediaRecorder.isTypeSupported(type)) || "";
}

function stopMediaStream() {
  if (!mediaStream) return;
  for (const track of mediaStream.getTracks()) {
    track.stop();
  }
  mediaStream = null;
}

function stopRecordingTimer() {
  clearInterval(recordingTimerId);
  recordingTimerId = null;
}

function setRecordingState(state, message) {
  recordingStatus.textContent = message;
  liveWaveform.classList.toggle("recording", state === "recording");
  liveWaveform.classList.toggle("ready", state === "ready");
}

function buildRecordingName() {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const extension = recordingMimeType().includes("mp4") ? "mp4" : "webm";
  return `live-recording-${stamp}.${extension}`;
}

async function startRecording() {
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    setRecordingState("error", "Recording is not available in this browser.");
    return;
  }
  try {
    recordedBlob = null;
    recordedName = "";
    recordedChunks = [];
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = recordingMimeType();
    mediaRecorder = new MediaRecorder(mediaStream, mimeType ? { mimeType } : undefined);
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data && event.data.size) {
        recordedChunks.push(event.data);
      }
    });
    mediaRecorder.addEventListener("stop", () => {
      const blobType = mediaRecorder.mimeType || mimeType || "audio/webm";
      recordedBlob = new Blob(recordedChunks, { type: blobType });
      recordedName = buildRecordingName();
      mediaRecorder = null;
      stopMediaStream();
      stopRecordingTimer();
      recordingTitle.textContent = recordedName;
      setRecordingState("ready", `Recorded ${formatClock((Date.now() - recordingStartedAt) / 1000)}. Source audio will be saved with the job.`);
      updatePrimaryAction();
    });
    recordingStartedAt = Date.now();
    recordingTimer.textContent = "00:00";
    recordingTimerId = setInterval(() => {
      recordingTimer.textContent = formatClock((Date.now() - recordingStartedAt) / 1000);
    }, 250);
    mediaRecorder.start();
    setRecordingState("recording", "Recording");
    updatePrimaryAction();
  } catch (error) {
    stopMediaStream();
    mediaRecorder = null;
    stopRecordingTimer();
    setRecordingState("error", error.message || "Microphone permission was not granted.");
    updatePrimaryAction();
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    setRecordingState("saving", "Saving recording");
  }
  updatePrimaryAction();
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
  gpuUsage.textContent = "Metal";
}

function renderJob(job) {
  jobPanel.hidden = false;
  jobTitle.textContent = job.message || job.status;
  const sourceLabel = job.source_name ? `${job.source_type || "file"} · ${job.source_name}` : job.source_type || "file";
  const languageLabel = job.language_label || "Language pending";
  const formatLabel = job.output_format_label || "Output pending";
  jobMeta.textContent = `${sourceLabel} · ${languageLabel} · ${formatLabel}`;
  savedPath.textContent = job.output_location ? `Saved to ${job.output_location}` : "";
  sourcePath.textContent = job.source_path ? `Source stored at ${job.source_path}` : "";
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
  if (job.saved_source_filename) {
    const sourceLink = document.createElement("a");
    sourceLink.href = `/download/${job.id}/${encodeURIComponent(job.saved_source_filename)}`;
    sourceLink.textContent = job.source_type === "live" ? "Source recording" : "Source audio";
    downloads.appendChild(sourceLink);
  }

  if (job.status === "done") {
    setBusy(false);
    spinner.classList.add("done");
    barFill.style.transform = "scaleX(1)";
    setStatus("Ready", "ready");
    clearInterval(pollTimer);
  } else if (job.status === "failed" || job.status === "cancelled") {
    setBusy(false);
    spinner.classList.add("done");
    // textContent, not innerHTML — job.error is server text and must never be
    // interpreted as HTML.
    jobTitle.textContent = "";
    const span = document.createElement("span");
    span.className = "error";
    span.textContent = job.error || job.message || "Stopped";
    jobTitle.appendChild(span);
    setStatus("Ready", "ready");
    clearInterval(pollTimer);
  } else if (job.status === "paused") {
    spinner.classList.add("done");
    setStatus("Paused", "paused");
  } else {
    // queued / preparing / running / finalizing / cancelling — keep the pill in
    // sync so it can't get stuck on a stale "Paused" after a resume.
    spinner.classList.remove("done");
    setStatus(job.status === "cancelling" ? "Cancelling" : "Busy", "busy");
  }
}

async function pollJob(jobId) {
  // Tolerate transient hiccups; only declare the job lost after several
  // consecutive failures so one dropped request doesn't kill a live job.
  try {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) throw new Error(`status ${response.status}`);
    const job = await response.json();
    pollFailures = 0;
    renderJob(job);
  } catch (error) {
    pollFailures += 1;
    if (pollFailures >= 3) {
      renderJob({ status: "failed", error: "Lost connection to the local service.", log: [], files: {} });
    }
  }
}

async function controlJob(action) {
  if (!currentJobId) return;
  // A failed control request does not mean the job itself failed, so surface a
  // transient notice and let polling reflect the true state — don't nuke the job.
  try {
    const response = await fetch(`/api/jobs/${currentJobId}/${action}`, { method: "POST" });
    const job = await response.json();
    if (!response.ok) throw new Error(job.error || `status ${response.status}`);
    renderJob(job);
  } catch (error) {
    setStatus(`Could not ${action}`, "error");
  }
}

audioInput.addEventListener("change", setFileLabel);
sourceUrl.addEventListener("input", updatePrimaryAction);
recordButton.addEventListener("click", startRecording);
stopRecordButton.addEventListener("click", stopRecording);

for (const button of sourceButtons) {
  button.addEventListener("click", () => switchSource(button.dataset.source));
}

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
  if (!sourceReady()) return;
  if (currentSource === "live" && (!recordedBlob || recordedBlob.size === 0)) {
    setRecordingState("error", "That recording is empty — record again.");
    return;
  }

  setBusy(true);
  spinner.classList.remove("done");
  downloads.innerHTML = "";
  log.textContent = "";
  setStatus("Busy", "busy");
  jobPanel.hidden = false;
  jobTitle.textContent = "Uploading";
  jobMeta.textContent = "Preparing";
  barFill.style.transform = "scaleX(0.08)";

  const body = new FormData(form);
  body.set("source_type", currentSource);
  if (currentSource === "url") {
    body.delete("audio");
  } else if (currentSource === "live") {
    body.delete("audio");
    body.set("audio", recordedBlob, recordedName || "live-recording.webm");
  }
  let response;
  let job;
  try {
    response = await fetch("/api/jobs", { method: "POST", body });
    job = await response.json();
  } catch (error) {
    renderJob({ status: "failed", error: "Could not reach the local service.", log: [], files: {} });
    return;
  }
  if (!response.ok) {
    renderJob({ status: "failed", error: job.error || "Upload failed", log: [], files: {} });
    return;
  }

  renderJob(job);
  currentJobId = job.id;
  pollFailures = 0;
  clearInterval(pollTimer);
  pollTimer = setInterval(() => pollJob(job.id), 2500);

  // Consume the live recording so it can't be silently re-submitted to a 2nd job.
  if (currentSource === "live") {
    recordedBlob = null;
    recordedName = "";
    recordedChunks = [];
    setRecordingState("idle", "Ready when you are.");
    updatePrimaryAction();
  }
});

pauseButton.addEventListener("click", () => controlJob("pause"));
resumeButton.addEventListener("click", () => controlJob("resume"));
terminateButton.addEventListener("click", () => controlJob("terminate"));
installButton.addEventListener("click", () => {
  if (installDialog.showModal) {
    installDialog.showModal();
  }
});
// Inside the native .app shell there is no browser to "install" into, so hide
// the PWA add-to-dock button. pywebview exposes window.pywebview; it may be
// injected just after this script runs, so also re-check on pywebviewready.
function hideInstallButtonInNativeShell() {
  if (typeof window.pywebview !== "undefined") {
    installButton.hidden = true;
  }
}
hideInstallButtonInNativeShell();
window.addEventListener("pywebviewready", hideInstallButtonInNativeShell);
browserInstallButton.addEventListener("click", async () => {
  if (!deferredInstallPrompt) return;
  try {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
  } catch (error) {
    // Ignore — the prompt was dismissed or is unavailable.
  }
  deferredInstallPrompt = null;
  browserInstallButton.hidden = true;
});
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  browserInstallButton.hidden = false;
});
updatePrimaryAction();

// ── App Translocation warning ────────────────────────────────────────────────
// If macOS is running a downloaded copy from a temporary mount, the bundled
// engine can't run; tell the user to move the app to /Applications.
const moveBanner = document.getElementById("moveBanner");
if (moveBanner) {
  fetch("/api/health")
    .then((r) => r.json())
    .then((h) => {
      if (h.translocated) moveBanner.hidden = false;
    })
    .catch(() => {});
}

// ── First-run model download ─────────────────────────────────────────────────
// Shown only when the model is missing (server renders #setupPanel). Lets the
// user download the large-v3 model in-app, with resumable progress, instead of
// a manual script. Re-enables Start when the model is ready.
const setupPanel = document.getElementById("setupPanel");
if (setupPanel) {
  const setupMessage = document.getElementById("setupMessage");
  const setupBar = document.getElementById("setupBar");
  const setupBarFill = document.getElementById("setupBarFill");
  const setupStats = document.getElementById("setupStats");
  const setupPercent = document.getElementById("setupPercent");
  const setupBytes = document.getElementById("setupBytes");
  const setupSpeed = document.getElementById("setupSpeed");
  const setupEta = document.getElementById("setupEta");
  const downloadModelButton = document.getElementById("downloadModelButton");
  const cancelDownloadButton = document.getElementById("cancelDownloadButton");

  const formatBytes = (n) => {
    if (!n) return "0 MB";
    const gb = n / 1e9;
    return gb >= 1 ? `${gb.toFixed(2)} GB` : `${Math.round(n / 1e6)} MB`;
  };
  const formatEta = (s) => {
    if (s == null) return "—";
    s = Math.round(s);
    if (s >= 3600) return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
    if (s >= 60) return `${Math.floor(s / 60)}m ${s % 60}s`;
    return `${s}s`;
  };

  function showDownloading(active) {
    setupBar.hidden = !active;
    setupStats.hidden = !active;
    downloadModelButton.hidden = active;
    cancelDownloadButton.hidden = !active;
  }

  function renderSetup(state) {
    const total = state.total || 0;
    const ratio = total ? Math.max(0.02, Math.min(1, state.downloaded / total)) : 0.02;
    setupBarFill.style.transform = `scaleX(${ratio})`;
    setupPercent.textContent = `${(state.percent || 0).toFixed(0)}%`;
    setupBytes.textContent = total ? `${formatBytes(state.downloaded)} / ${formatBytes(total)}` : "—";
    setupSpeed.textContent = state.speed_bps ? `${formatBytes(state.speed_bps)}/s` : "—";
    setupEta.textContent = state.status === "verifying" ? "verifying" : formatEta(state.eta_seconds);
  }

  function finishSetup() {
    clearInterval(setupPollTimer);
    setupPollTimer = null;
    modelReady = true;
    startButton.disabled = false;
    setupPanel.hidden = true;
    setStatus("Ready", "ready");
    updatePrimaryAction();
  }

  function failSetup(state) {
    clearInterval(setupPollTimer);
    setupPollTimer = null;
    showDownloading(false);
    const byKind = {
      offline: "Couldn’t reach the download server. Check your internet connection, then retry.",
      disk_full: "Not enough free disk space — free up about 3 GB, then retry.",
      checksum: "The download was corrupted. Retry to start it again from scratch.",
      http: "The download server returned an error. Please retry in a moment.",
    };
    const message = byKind[state.error_kind] || state.error || "Download failed.";
    setupMessage.textContent = "";
    const span = document.createElement("span");
    span.className = "error";
    span.textContent = message;  // textContent, never innerHTML, for server text
    setupMessage.appendChild(span);
    downloadModelButton.hidden = false;
    downloadModelButton.textContent = "Retry download";
  }

  async function pollSetup() {
    let state;
    try {
      const response = await fetch("/api/setup/status");
      state = await response.json();
    } catch (error) {
      return; // transient; next tick retries
    }
    if (state.ready || state.status === "done") return finishSetup();
    if (state.status === "error") return failSetup(state);
    if (state.status === "cancelled") {
      clearInterval(setupPollTimer);
      setupPollTimer = null;
      showDownloading(false);
      downloadModelButton.textContent = "Download model (2.9 GB)";
      return;
    }
    renderSetup(state);
  }

  function beginPolling() {
    showDownloading(true);
    clearInterval(setupPollTimer);
    setupPollTimer = setInterval(pollSetup, 1000);
  }

  async function startModelDownload() {
    downloadModelButton.textContent = "Download model (2.9 GB)";
    beginPolling();
    try {
      const response = await fetch("/api/setup/start", { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        failSetup({ error: body.error || "Could not start the download." });
      }
    } catch (error) {
      failSetup({ error_kind: "offline" });
    }
  }

  downloadModelButton.addEventListener("click", startModelDownload);
  cancelDownloadButton.addEventListener("click", () => {
    fetch("/api/setup/cancel", { method: "POST" }).catch(() => {});
  });

  // Resume a download already in progress (e.g. the window was reopened).
  fetch("/api/health")
    .then((r) => r.json())
    .then((h) => {
      if (h.ready) return finishSetup();
      if (h.setup_status === "downloading" || h.setup_status === "verifying") beginPolling();
    })
    .catch(() => {});
}
