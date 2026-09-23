import assert from "node:assert/strict";
import test from "node:test";
import { loadHelp } from "../_support/web_extension.mjs";

test("execution errors display Japanese guidance and original error without removed UI", async () => {
  const { extension, listeners, document } = await loadHelp("error_support");
  await extension.setup();
  assert.deepEqual(Object.keys(listeners), ["execution_error"]);
  listeners.execution_error({ detail: {
    exception_type: "OutOfMemoryError", exception_message: "CUDA out of memory", node_type: "KSampler",
  } });
  const text = document.body.text();
  assert.match(text, /VRAM/);
  assert.match(text, /CUDA out of memory/);
  assert.match(text, /KSampler/);
  assert.doesNotMatch(text, /プリセット|テンプレートを開く|Promptタグ/);
});
