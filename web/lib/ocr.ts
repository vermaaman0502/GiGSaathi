/** On-device OCR via tesseract.js (loaded on demand). Nothing is uploaded to a server: the image stays in the browser.
 *  Language data is downloaded once from the tesseract CDN, so the first run needs a connection. */
export async function ocrImage(file: File, lang: string, onProgress: (pct: number, status: string) => void): Promise<string> {
  const { createWorker } = await import("tesseract.js");
  const langs = lang === "hi" ? "eng+hin" : lang === "pa" ? "eng+pan" : "eng";
  const worker = await createWorker(langs, 1, { logger: (m: { progress: number; status: string }) => onProgress(Math.round((m.progress || 0) * 100), m.status) });
  try {
    const { data } = await worker.recognize(file);
    return data.text;
  } finally {
    await worker.terminate();
  }
}
