"use client";

// Puter.js + Mistral OCR runs only in the browser and keeps page provenance.
const RENDER_SCALE = 2.0;
const MIN_RENDER_SCALE = 0.6;
const MAX_IMAGE_BYTES = 9.5 * 1024 * 1024;

let _puterPromise = null;
let _pdfjsPromise = null;

async function getPuter() {
  if (!_puterPromise) {
    _puterPromise = import("@heyputer/puter.js").then((mod) => {
      const puter = mod.default || mod.puter || (typeof window !== "undefined" ? window.puter : null);
      if (!puter?.ai?.img2txt) throw new Error("Puter.js OCR is unavailable in this browser");
      return puter;
    });
  }
  return _puterPromise;
}

async function getPdfjs() {
  if (!_pdfjsPromise) {
    _pdfjsPromise = import("pdfjs-dist").then((pdfjs) => {
      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        "pdfjs-dist/build/pdf.worker.min.mjs",
        import.meta.url
      ).toString();
      return pdfjs;
    });
  }
  return _pdfjsPromise;
}

async function renderPageToPng(page, scale) {
  const viewport = page.getViewport({ scale });
  const canvas = document.createElement("canvas");
  canvas.width = Math.ceil(viewport.width);
  canvas.height = Math.ceil(viewport.height);
  const ctx = canvas.getContext("2d", { alpha: false });
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  await page.render({ canvasContext: ctx, viewport }).promise;
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  canvas.width = 0;
  canvas.height = 0;
  return blob;
}

async function pageToBoundedPng(page) {
  let scale = RENDER_SCALE;
  let blob = await renderPageToPng(page, scale);
  while (blob && blob.size > MAX_IMAGE_BYTES && scale > MIN_RENDER_SCALE) {
    scale *= 0.75;
    blob = await renderPageToPng(page, scale);
  }
  return blob;
}

export async function runMistralOcr(pdfData, { onProgress, signal } = {}) {
  const [pdfjs, puter] = await Promise.all([getPdfjs(), getPuter()]);

  const doc = await pdfjs.getDocument({ data: pdfData, isEvalSupported: false }).promise;
  const pages = [];
  try {
    for (let pageNumber = 1; pageNumber <= doc.numPages; pageNumber += 1) {
      if (signal?.aborted) {
        const err = new Error("OCR cancelled");
        err.name = "AbortError";
        throw err;
      }
      const page = await doc.getPage(pageNumber);
      let text = "";
      try {
        const blob = await pageToBoundedPng(page);
        if (blob) {
          text = await puter.ai.img2txt({ source: blob, provider: "mistral" });
        }
      } finally {
        page.cleanup();
      }
      if (text && String(text).trim()) {
        pages.push({ page_number: pageNumber, text: String(text).trim() });
      }
      onProgress?.({ done: pageNumber, total: doc.numPages });
    }
  } finally {
    doc.destroy();
  }

  if (!pages.length) {
    throw new Error("OCR produced no readable text on any page");
  }
  return pages;
}
