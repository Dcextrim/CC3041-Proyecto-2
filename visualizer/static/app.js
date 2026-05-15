const viewModeEl = document.getElementById("viewMode");
const algorithmEl = document.getElementById("algorithm");
const graphTypeEl = document.getElementById("graphType");
const nEl = document.getElementById("n");
const pEl = document.getElementById("p");
const seedEl = document.getElementById("seed");
const speedEl = document.getElementById("speed");
const orderModeEl = document.getElementById("orderMode");

const runBtn = document.getElementById("runBtn");
const pauseBtn = document.getElementById("pauseBtn");
const stepBtn = document.getElementById("stepBtn");
const resetBtn = document.getElementById("resetBtn");

const progressBar = document.getElementById("progressBar");
const statusText = document.getElementById("statusText");
const eventText = document.getElementById("eventText");
const graphLabel = document.getElementById("graphLabel");
const verticesText = document.getElementById("vertices");
const edgesText = document.getElementById("edges");
const colorsUsedText = document.getElementById("colorsUsed");
const timingCard = document.getElementById("timingCard");
const stepCounter = document.getElementById("stepCounter");
const legend = document.getElementById("legend");

const singleStage = document.getElementById("singleStage");
const compareStage = document.getElementById("compareStage");

const singleCanvas = document.getElementById("graphCanvas");
const greedyCanvas = document.getElementById("greedyCanvas");
const dpCanvas = document.getElementById("dpCanvas");

const singleCtx = singleCanvas.getContext("2d");
const greedyCtx = greedyCanvas.getContext("2d");
const dpCtx = dpCanvas.getContext("2d");

const palette = [
  "#7f3b08", "#b35806", "#e08214", "#fdb863", "#fee0b6",
  "#d8daeb", "#b2abd2", "#8073ac", "#542788", "#2d004b",
  "#00441b", "#1b7837", "#5aae61", "#a6dba0", "#d9f0d3",
  "#a50f15", "#de2d26", "#fb6a4a", "#fcae91", "#fee5d9",
  "#08519c", "#3182bd", "#6baed6", "#9ecae1", "#deebf7"
];

const state = {
  mode: "single",
  running: false,
  paused: false,
  timer: null,
  single: {
    nodes: [],
    edges: [],
    steps: [],
    stepIndex: 0,
    nodeColors: {},
    meta: null,
  },
  compare: {
    nodes: [],
    edges: [],
    meta: null,
    greedy: {
      steps: [],
      stepIndex: 0,
      nodeColors: {},
      meta: null,
      progress: 0,
      lastMessage: "",
    },
    dp: {
      steps: [],
      stepIndex: 0,
      nodeColors: {},
      meta: null,
      progress: 0,
      lastMessage: "",
    },
  },
};

function colorForIndex(index) {
  if (Number.isNaN(index) || index === null || index === undefined) {
    return "#c9d3d7";
  }
  if (index < palette.length) {
    return palette[index];
  }
  const hue = (index * 47) % 360;
  return `hsl(${hue} 70% 45%)`;
}

function resizeOneCanvas(canvas, ctx) {
  if (!canvas || !ctx) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.max(100, Math.floor(rect.width * dpr));
  canvas.height = Math.max(100, Math.floor(rect.height * dpr));
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function resizeAllCanvases() {
  resizeOneCanvas(singleCanvas, singleCtx);
  resizeOneCanvas(greedyCanvas, greedyCtx);
  resizeOneCanvas(dpCanvas, dpCtx);
  drawActiveView();
}

function graphCoordToCanvas(node, canvas) {
  const margin = 30;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  return {
    x: margin + node.x * (w - 2 * margin),
    y: margin + node.y * (h - 2 * margin),
  };
}

function drawGraphTo(ctx, canvas, nodes, edges, nodeColors, emptyText) {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;

  ctx.clearRect(0, 0, w, h);

  if (!nodes.length) {
    ctx.fillStyle = "#738489";
    ctx.font = "16px Segoe UI";
    ctx.fillText(emptyText, 24, 32);
    return;
  }

  const nodeLookup = new Map(nodes.map((node) => [node.id, node]));

  ctx.lineWidth = 1.4;
  ctx.strokeStyle = "#a4b3b8";
  for (const edge of edges) {
    const sourceNode = nodeLookup.get(edge.source);
    const targetNode = nodeLookup.get(edge.target);
    if (!sourceNode || !targetNode) {
      continue;
    }

    const source = graphCoordToCanvas(sourceNode, canvas);
    const target = graphCoordToCanvas(targetNode, canvas);
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);
    ctx.stroke();
  }

  const nodeRadius = nodes.length > 70 ? 9 : 12;

  for (const node of nodes) {
    const point = graphCoordToCanvas(node, canvas);
    const colorIndex = nodeColors[node.id];
    const fill = colorForIndex(colorIndex);

    ctx.beginPath();
    ctx.arc(point.x, point.y, nodeRadius, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.lineWidth = 1.3;
    ctx.strokeStyle = "#37474f";
    ctx.stroke();

    ctx.fillStyle = "#102027";
    ctx.font = nodes.length > 80 ? "10px Segoe UI" : "12px Segoe UI";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(node.label, point.x, point.y);
  }
}

function drawActiveView() {
  if (state.mode === "single") {
    drawGraphTo(
      singleCtx,
      singleCanvas,
      state.single.nodes,
      state.single.edges,
      state.single.nodeColors,
      "No hay grafo cargado"
    );
    return;
  }

  drawGraphTo(
    greedyCtx,
    greedyCanvas,
    state.compare.nodes,
    state.compare.edges,
    state.compare.greedy.nodeColors,
    "Greedy sin datos"
  );

  drawGraphTo(
    dpCtx,
    dpCanvas,
    state.compare.nodes,
    state.compare.edges,
    state.compare.dp.nodeColors,
    "DP sin datos"
  );
}

function legendHtmlForColors(title, nodeColors) {
  const used = new Map();
  for (const [nodeId, colorIndex] of Object.entries(nodeColors)) {
    if (!used.has(colorIndex)) {
      used.set(colorIndex, []);
    }
    used.get(colorIndex).push(nodeId);
  }

  if (!used.size) {
    return `
      <div class="legend-block">
        <strong>${title}</strong>
        <div class="legend-item">
          <span class="legend-swatch" style="background:#c9d3d7"></span>
          <span>Sin color</span>
        </div>
      </div>
    `;
  }

  const items = [...used.entries()]
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([colorIndex, nodes]) => {
      const swatch = colorForIndex(Number(colorIndex));
      const sample = nodes.slice(0, 6).join(", ");
      const suffix = nodes.length > 6 ? ` ... (+${nodes.length - 6})` : "";
      return `
        <div class="legend-item">
          <span class="legend-swatch" style="background:${swatch}"></span>
          <span>Color ${colorIndex}: ${sample}${suffix}</span>
        </div>
      `;
    })
    .join("");

  return `<div class="legend-block"><strong>${title}</strong>${items}</div>`;
}

function updateLegend() {
  if (state.mode === "single") {
    legend.innerHTML = legendHtmlForColors("Leyenda", state.single.nodeColors);
    return;
  }

  legend.innerHTML =
    legendHtmlForColors("Greedy", state.compare.greedy.nodeColors) +
    legendHtmlForColors("DP", state.compare.dp.nodeColors);
}

function setProgress(progress) {
  const bounded = Math.max(0, Math.min(1, progress));
  progressBar.style.width = `${(bounded * 100).toFixed(1)}%`;
}

function setStatus(text, isError = false) {
  statusText.textContent = text;
  statusText.style.color = isError ? "#b74a4a" : "#132026";
}

function setEvent(text) {
  eventText.textContent = text;
}

function hasLoadedData() {
  if (state.mode === "single") {
    return state.single.steps.length > 0;
  }
  return state.compare.greedy.steps.length > 0 || state.compare.dp.steps.length > 0;
}

function renderTimingCard(mode, msA, msB) {
  if (mode === "single") {
    timingCard.innerHTML = `<span class="t-pill">${msA} ms</span>`;
    return;
  }

  const faster = msA <= msB;
  const ratio = msA > 0 ? (msB / msA).toFixed(1) : "–";
  const speedupHtml = msB > msA
    ? `<div class="t-speedup">DP tarda <strong>${ratio}×</strong> más</div>`
    : msA > msB
      ? `<div class="t-speedup">Greedy tarda <strong>${(msA / msB).toFixed(1)}×</strong> más</div>`
      : `<div class="t-speedup">Tiempo similar</div>`;

  timingCard.innerHTML = `
    <div class="timing-compare">
      <div class="t-block${msA > msB ? " slower" : ""}">
        <span class="t-algo">Greedy</span>
        <span class="t-val">${msA} ms</span>
      </div>
      <div class="t-block${msB > msA ? " slower" : ""}">
        <span class="t-algo">DP</span>
        <span class="t-val">${msB} ms</span>
      </div>
    </div>
    ${speedupHtml}
  `;
}

function updateButtons() {
  runBtn.disabled = state.running;
  pauseBtn.disabled = !state.running;
  stepBtn.disabled = !state.running;
  resetBtn.disabled = !state.running && !hasLoadedData();
  pauseBtn.textContent = state.paused ? "Reanudar" : "Pausar";
}

function updateStepCounter() {
  if (state.mode === "single") {
    stepCounter.textContent = `${state.single.stepIndex}/${state.single.steps.length}`;
    return;
  }

  stepCounter.textContent =
    `G ${state.compare.greedy.stepIndex}/${state.compare.greedy.steps.length} | ` +
    `DP ${state.compare.dp.stepIndex}/${state.compare.dp.steps.length}`;
}

function stopTimer() {
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
}

function finishRun() {
  stopTimer();
  state.running = false;
  state.paused = false;
  updateButtons();
  setStatus("Finalizado");
}

function resetSingleState() {
  state.single.nodes = [];
  state.single.edges = [];
  state.single.steps = [];
  state.single.stepIndex = 0;
  state.single.nodeColors = {};
  state.single.meta = null;
}

function resetCompareState() {
  state.compare.nodes = [];
  state.compare.edges = [];
  state.compare.meta = null;

  state.compare.greedy.steps = [];
  state.compare.greedy.stepIndex = 0;
  state.compare.greedy.nodeColors = {};
  state.compare.greedy.meta = null;
  state.compare.greedy.progress = 0;
  state.compare.greedy.lastMessage = "";

  state.compare.dp.steps = [];
  state.compare.dp.stepIndex = 0;
  state.compare.dp.nodeColors = {};
  state.compare.dp.meta = null;
  state.compare.dp.progress = 0;
  state.compare.dp.lastMessage = "";
}

function resetVisualization() {
  stopTimer();
  state.running = false;
  state.paused = false;

  resetSingleState();
  resetCompareState();

  graphLabel.textContent = "-";
  verticesText.textContent = "-";
  edgesText.textContent = "-";
  colorsUsedText.textContent = "-";
  timingCard.innerHTML = '<span class="t-pill">–</span>';

  setStatus("Listo");
  setEvent("Configura parametros y presiona Ejecutar.");
  setProgress(0);
  updateStepCounter();
  drawActiveView();
  updateLegend();
  updateButtons();
}

function applySingleStep(step) {
  if (!step) {
    return;
  }

  if (step.coloring) {
    state.single.nodeColors = { ...state.single.nodeColors, ...step.coloring };
  }

  if (step.progress !== undefined) {
    setProgress(step.progress);
  } else {
    setProgress(state.single.stepIndex / Math.max(state.single.steps.length, 1));
  }

  if (step.message) {
    setEvent(step.message);
  }

  drawActiveView();
  updateLegend();
}

function stepSingleForward() {
  if (state.single.stepIndex >= state.single.steps.length) {
    finishRun();
    return;
  }

  const step = state.single.steps[state.single.stepIndex];
  state.single.stepIndex += 1;

  applySingleStep(step);
  updateStepCounter();

  if (state.single.stepIndex >= state.single.steps.length) {
    finishRun();
  }
}

function applyCompareStep(channel) {
  const block = state.compare[channel];
  if (block.stepIndex >= block.steps.length) {
    return false;
  }

  const step = block.steps[block.stepIndex];
  block.stepIndex += 1;

  if (step.coloring) {
    block.nodeColors = { ...block.nodeColors, ...step.coloring };
  }

  if (step.progress !== undefined) {
    block.progress = step.progress;
  } else {
    block.progress = block.stepIndex / Math.max(block.steps.length, 1);
  }

  if (step.message) {
    block.lastMessage = step.message;
  }

  return true;
}

function stepCompareForward() {
  const movedGreedy = applyCompareStep("greedy");
  const movedDp = applyCompareStep("dp");

  const progress = (state.compare.greedy.progress + state.compare.dp.progress) / 2;
  setProgress(progress);

  const gMsg = state.compare.greedy.lastMessage || "sin cambios";
  const dMsg = state.compare.dp.lastMessage || "sin cambios";
  setEvent(`Greedy: ${gMsg} | DP: ${dMsg}`);

  drawActiveView();
  updateLegend();
  updateStepCounter();

  const greedyDone = state.compare.greedy.stepIndex >= state.compare.greedy.steps.length;
  const dpDone = state.compare.dp.stepIndex >= state.compare.dp.steps.length;

  if ((greedyDone && dpDone) || (!movedGreedy && !movedDp)) {
    finishRun();
  }
}

function stepForward() {
  if (state.mode === "single") {
    stepSingleForward();
  } else {
    stepCompareForward();
  }
}

function startAnimation() {
  stopTimer();

  const speedMs = Math.max(20, Number(speedEl.value) || 260);
  state.running = true;
  state.paused = false;

  setStatus(state.mode === "single" ? "Ejecutando" : "Ejecutando comparativo");
  updateButtons();

  state.timer = setInterval(() => {
    if (state.paused) {
      return;
    }
    stepForward();
  }, speedMs);
}

function syncControlHints() {
  state.mode = viewModeEl.value;

  const mode = state.mode;
  const algorithm = algorithmEl.value;
  const graphType = graphTypeEl.value;

  const isCompare = mode === "compare";
  algorithmEl.disabled = isCompare;

  let maxN;
  if (isCompare) {
    maxN = graphType === "crown" ? 9 : 18;
  } else if (algorithm === "dp") {
    maxN = graphType === "crown" ? 9 : 18;
  } else {
    maxN = graphType === "crown" ? 70 : 140;
  }

  nEl.max = String(maxN);
  if (Number(nEl.value) > maxN) {
    nEl.value = maxN;
  }
  if (Number(nEl.value) < 3) {
    nEl.value = 3;
  }

  pEl.disabled = graphType !== "random";

  const crown = graphType === "crown";
  const greedyActive = isCompare || algorithm === "greedy";
  orderModeEl.disabled = !greedyActive;

  if (!crown && (orderModeEl.value === "bad" || orderModeEl.value === "good")) {
    orderModeEl.value = "ldf";
  }

  singleStage.classList.toggle("hidden", isCompare);
  compareStage.classList.toggle("hidden", !isCompare);

  requestAnimationFrame(() => {
    resizeAllCanvases();
    updateStepCounter();
  });
}

function applyCommonStats(meta) {
  graphLabel.textContent = meta.graphLabel;
  verticesText.textContent = meta.n;
  edgesText.textContent = meta.m;
}

function handleRunError(error) {
  setStatus("Error", true);
  setEvent(error.message || String(error));
  stopTimer();
  state.running = false;
  state.paused = false;
  updateButtons();
}

async function runSingle(payload) {
  const response = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "No se pudo ejecutar la simulacion.");
  }

  resetSingleState();
  resetCompareState();

  state.single.nodes = data.nodes || [];
  state.single.edges = data.edges || [];
  state.single.steps = data.steps || [];
  state.single.meta = data.meta || null;

  applyCommonStats(data.meta);
  colorsUsedText.textContent = data.meta.colorsUsed;
  renderTimingCard("single", data.meta.computeMs, null);

  setProgress(0);
  updateStepCounter();
  drawActiveView();
  updateLegend();

  if (!state.single.steps.length) {
    setStatus("Sin pasos", true);
    setEvent("El backend no devolvio eventos de animacion.");
    updateButtons();
    return;
  }

  startAnimation();
}

async function runCompare(payload) {
  const response = await fetch("/api/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "No se pudo ejecutar la comparacion.");
  }

  resetSingleState();
  resetCompareState();

  state.compare.nodes = data.nodes || [];
  state.compare.edges = data.edges || [];
  state.compare.meta = data.meta || null;

  state.compare.greedy.steps = data.greedy?.steps || [];
  state.compare.greedy.meta = data.greedy || null;

  state.compare.dp.steps = data.dp?.steps || [];
  state.compare.dp.meta = data.dp || null;

  applyCommonStats(data.meta);
  colorsUsedText.textContent = `G ${data.greedy.colorsUsed} | DP ${data.dp.colorsUsed}`;
  renderTimingCard("compare", data.greedy.computeMs, data.dp.computeMs);

  setProgress(0);
  updateStepCounter();
  drawActiveView();
  updateLegend();

  const hasSteps = state.compare.greedy.steps.length || state.compare.dp.steps.length;
  if (!hasSteps) {
    setStatus("Sin pasos", true);
    setEvent("La comparacion no devolvio eventos de animacion.");
    updateButtons();
    return;
  }

  startAnimation();
}

async function runVisualization() {
  stopTimer();
  state.running = false;
  state.paused = false;
  updateButtons();

  const payload = {
    algorithm: algorithmEl.value,
    graphType: graphTypeEl.value,
    n: Number(nEl.value),
    p: Number(pEl.value),
    seed: Number(seedEl.value),
    orderMode: orderModeEl.value,
  };

  setStatus("Consultando backend...");
  setEvent("Preparando grafo y pasos...");

  try {
    if (state.mode === "single") {
      await runSingle(payload);
    } else {
      await runCompare(payload);
    }
  } catch (error) {
    handleRunError(error);
  }
}

runBtn.addEventListener("click", runVisualization);

pauseBtn.addEventListener("click", () => {
  if (!state.running) {
    return;
  }

  state.paused = !state.paused;
  setStatus(state.paused ? "Pausado" : (state.mode === "single" ? "Ejecutando" : "Ejecutando comparativo"));
  updateButtons();
});

stepBtn.addEventListener("click", () => {
  if (!state.running) {
    return;
  }

  state.paused = true;
  setStatus("Pausado");
  updateButtons();
  stepForward();
});

resetBtn.addEventListener("click", resetVisualization);

viewModeEl.addEventListener("change", () => {
  syncControlHints();
  resetVisualization();
});

algorithmEl.addEventListener("change", () => {
  syncControlHints();
  resetVisualization();
});

graphTypeEl.addEventListener("change", () => {
  syncControlHints();
  resetVisualization();
});

window.addEventListener("resize", resizeAllCanvases);

syncControlHints();
resetVisualization();
resizeAllCanvases();
