import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { loadHelp } from '../_support/web_extension.mjs';

test('selected model descriptions follow selection and preserve existing help', async () => {
  const { extension } = await loadHelp('model_tooltips');
  extension.beforeRegisterNodeDef(null, {name: 'VAELoader', input: {required: {vae_name: [[], {tooltip: '標準の説明'}]}}});
  const widget = {name: 'vae_name', value: 'QwenImage\\qwen_image_2.1_vae_bf16.safetensors'};
  const node = {comfyClass: 'VAELoader', widgets: [widget]};
  extension.nodeCreated(node);
  assert.match(widget.tooltip, /Alibaba/);
  assert.match(widget.tooltip, /標準の説明/);
  const first = widget.tooltip;
  extension.loadedGraphNode(node);
  assert.equal(widget.tooltip, first);
  widget.value = 'SDXL/sdxlAnimeClearVae_clear.safetensors';
  assert.match(widget.tooltip, /easygoing0114/);
  assert.doesNotMatch(widget.tooltip, /Alibaba/);
  widget.value = 'elsewhere/sdxlAnimeClearVae_clear.safetensors';
  assert.match(widget.tooltip, /未登録/);
  widget.value = 'pixel_space';
  assert.equal(widget.tooltip, '標準の説明');
  widget.tooltip = '変更後の説明';
  assert.equal(widget.tooltip, '変更後の説明');
});

test('accessors and unrelated widgets retain their behavior', async () => {
  const {extension} = await loadHelp('model_tooltips');
  let help = '元の説明';
  const widget = {name: 'lora_name', value: 'Qwen/NSFW Qwen Lora.safetensors', get tooltip(){return help;}, set tooltip(value){help=value;}};
  const unrelated = {name: 'model_name', value: 'something.pth'};
  extension.nodeCreated({comfyClass: 'OtherNode', widgets: [widget, unrelated]});
  assert.match(widget.tooltip, /元の説明/);
  widget.tooltip = '更新';
  assert.equal(help, '更新');
  assert.match(widget.tooltip, /更新/);
  assert.equal(unrelated.tooltip, undefined);
  assert.equal(widget.value, 'Qwen/NSFW Qwen Lora.safetensors');
});

test('catalog entries have unique category-relative identities and required descriptions', async () => {
  const root = new URL('../../../../comfy_extras/jp_enhanced/model_tooltips/web/catalog/', import.meta.url);
  const manifest = JSON.parse(await readFile(new URL('index.json', root), 'utf8'));
  const keys = new Set();
  for (const file of manifest.files) {
    const group = JSON.parse(await readFile(new URL(file, root), 'utf8'));
    for (const entry of group.models) {
      const key = `${group.category}/${entry.file}`;
      assert.ok(!keys.has(key), key);
      keys.add(key);
      assert.ok(!entry.file.includes('\\') && !entry.file.startsWith('/') && !entry.file.includes('..'));
      for (const field of ['name','author','baseModel','description','verification']) assert.ok(entry[field], `${key}: ${field}`);
      assert.ok(Array.isArray(entry.sources));
      for (const url of entry.sources) assert.match(url, /^https:\/\//);
    }
  }
  assert.equal(keys.size, 39);
});
