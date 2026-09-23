import assert from "node:assert/strict";
import test from "node:test";
import { loadHelp } from "../_support/web_extension.mjs";

test("Japanese node descriptions preserve original explanations and unknown nodes", async () => {
  const { extension } = await loadHelp("node_tooltips");
  const known = { name: "KSampler", description: "Original explanation" };
  extension.beforeRegisterNodeDef({}, known);
  assert.match(known.description, /画像生成/);
  assert.match(known.description, /Original explanation/);
  const unknown = { name: "UnlistedCustomNode", description: "Keep me" };
  extension.beforeRegisterNodeDef({}, unknown);
  assert.equal(unknown.description, "Keep me");
});

