// The live fragment: a real model's real score map, re-thresholded in the browser.
// Data: public/demo/demo.json and the half-resolution maps written by scripts/export_demo.py.
// Without JavaScript the fragment shows the photo with a pre-rendered mask (the <noscript> image).

const root = document.querySelector(".detector");
const canvas = root?.querySelector(".detector__mask");

if (root && canvas) {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, "/");
  const $ = (selector) => document.querySelector(selector);
  const ui = {
    photo: root.querySelector(".detector__photo"),
    model: $('[data-control="model"]'),
    threshold: $('[data-control="threshold"]'),
    reset: $('[data-control="reset"]'),
    truth: $('[data-control="truth"]'),
    out: Object.fromEntries([...document.querySelectorAll("[data-out]")].map((el) => [el.dataset.out, el])),
    photos: [...root.querySelectorAll("[data-photo]")],
  };
  const MASK = [229, 72, 77];      // the product's mask colour (--ui-mask)
  const TRUTH = [47, 211, 196];    // the annotation outline (--ui-truth)
  const cache = new Map();
  const state = { demo: null, image: 0, model: null, threshold: 0, truth: false };

  const fetchBytes = async (path) => {
    if (!cache.has(path)) cache.set(path, fetch(base + path).then((r) => { if (!r.ok) throw new Error(path); return r.arrayBuffer(); }));
    return cache.get(path);
  };

  // Scores of one model on one photo, decoded from uint16 between the map's min and max
  async function scores(model, frame) {
    const [lo, hi] = model.ranges[frame];
    const q = new Uint16Array(await fetchBytes(model.maps[frame]));
    const out = new Float32Array(q.length);
    for (let i = 0; i < q.length; i++) out[i] = lo + (q[i] / 65535) * (hi - lo);
    return out;
  }

  // Threshold, then drop 8-connected blobs smaller than the model's minimum (as postprocessing.to_masks)
  function toMask(values, threshold, minBlob, width, height) {
    const mask = new Uint8Array(values.length);
    for (let i = 0; i < values.length; i++) mask[i] = values[i] >= threshold ? 1 : 0;
    const seen = new Uint8Array(mask.length), stack = new Int32Array(mask.length), blob = [];
    let blobs = 0;
    for (let start = 0; start < mask.length; start++) {
      if (!mask[start] || seen[start]) continue;
      let top = 0; stack[top++] = start; seen[start] = 1; blob.length = 0;
      while (top) {
        const p = stack[--top]; blob.push(p);
        const x = p % width, y = (p - x) / width;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = x + dx, ny = y + dy;
          if ((dx || dy) && nx >= 0 && ny >= 0 && nx < width && ny < height) {
            const n = ny * width + nx;
            if (mask[n] && !seen[n]) { seen[n] = 1; stack[top++] = n; }
          }
        }
      }
      if (blob.length < minBlob) for (const p of blob) mask[p] = 0; else blobs++;
    }
    return { mask, blobs };
  }

  function draw(mask, truth, width, height) {
    const ctx = canvas.getContext("2d");
    const img = ctx.createImageData(width, height);
    for (let i = 0; i < mask.length; i++) {
      const o = i * 4;
      if (mask[i]) { img.data.set(MASK, o); img.data[o + 3] = 150; }
      if (state.truth && truth[i]) {   // outline: annotated pixels with a background neighbour
        const x = i % width;
        const edge = !truth[i - 1] || !truth[i + 1] || !truth[i - width] || !truth[i + width] || x === 0 || x === width - 1;
        if (edge) { img.data.set(TRUTH, o); img.data[o + 3] = 255; }
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  function f1(mask, truth) {
    let tp = 0, fp = 0, fn = 0;
    for (let i = 0; i < mask.length; i++) { if (mask[i] && truth[i]) tp++; else if (mask[i]) fp++; else if (truth[i]) fn++; }
    return tp + fp + fn === 0 ? 1 : (2 * tp) / (2 * tp + fp + fn);
  }

  const digits = (model) => (model.unit === "probability" ? 3 : 2);

  async function render() {
    const { demo } = state;
    const [height, width] = demo.size;
    const image = demo.images[state.image];
    const model = state.model;
    const [values, truth] = await Promise.all([scores(model, image.frame), fetchBytes(image.gt).then((b) => new Uint8Array(b))]);
    const { mask, blobs } = toMask(values, state.threshold, model.min_blob_half, width, height);
    draw(mask, truth, width, height);
    const flagged = mask.reduce((s, v) => s + v, 0) / mask.length;
    ui.out.f1.textContent = f1(mask, truth).toFixed(2);
    ui.out.area.textContent = `${(100 * flagged).toFixed(1)} %`;
    ui.out.blobs.textContent = String(blobs);
    ui.out.threshold.textContent = state.threshold.toFixed(digits(model));
    ui.reset.hidden = Math.abs(state.threshold - model.threshold) < 1e-9;
  }

  function setModel(name, keepThreshold = false) {
    const model = state.demo.models.find((m) => m.name === name) ?? state.demo.models[0];
    state.model = model;
    const [lo, hi] = model.slider;
    Object.assign(ui.threshold, { min: String(lo), max: String(hi), step: String((hi - lo) / 400) });
    if (!keepThreshold) state.threshold = model.threshold;
    ui.threshold.value = String(state.threshold);
    ui.threshold.setAttribute("aria-valuetext", `${state.threshold.toFixed(digits(model))} (${model.unit})`);
  }

  function setImage(index) {
    state.image = index;
    const image = state.demo.images[index];
    ui.photo.src = base + image.photo;
    ui.photo.alt = image.title;
    ui.photos.forEach((b, i) => b.setAttribute("aria-pressed", String(i === index)));
  }

  let frame = 0;
  const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(() => render().catch(console.error)); };

  fetch(base + "demo/demo.json").then((r) => r.json()).then((demo) => {
    state.demo = demo;
    setModel(ui.model.value);
    schedule();
    ui.model.addEventListener("change", () => { setModel(ui.model.value); schedule(); });
    ui.threshold.addEventListener("input", () => {
      state.threshold = Number(ui.threshold.value);
      ui.threshold.setAttribute("aria-valuetext", `${state.threshold.toFixed(digits(state.model))} (${state.model.unit})`);
      schedule();
    });
    ui.reset.addEventListener("click", () => { setModel(state.model.name); schedule(); });
    ui.truth.addEventListener("click", () => {
      state.truth = !state.truth;
      ui.truth.setAttribute("aria-pressed", String(state.truth));
      schedule();
    });
    ui.photos.forEach((button, i) => button.addEventListener("click", () => { setImage(i); schedule(); }));
  }).catch(() => { root.classList.add("is-static"); });

  // Showcase: one report per model, swapped with a short crossfade
  const names = [...document.querySelectorAll("[data-report]")];
  const sheets = [...document.querySelectorAll("[data-sheet]")];
  names.forEach((button) => button.addEventListener("click", () => {
    names.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
    sheets.forEach((sheet) => {
      const show = sheet.dataset.sheet === button.dataset.report;
      sheet.hidden = !show;   // the crossfade itself is a GSAP tween (motion.js)
    });
  }));
}
