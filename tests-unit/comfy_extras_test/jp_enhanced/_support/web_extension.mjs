import { readFile } from "node:fs/promises";
import vm from "node:vm";

const directory = new URL("../../../../comfy_extras/jp_enhanced/", import.meta.url);

class Element {
  children = [];
  textContent = "";
  listeners = {};
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  querySelector() { return null; }
  setAttribute() {}
  addEventListener(name, listener) { this.listeners[name] = listener; }
  remove() {}
  text() { return this.textContent + this.children.map((child) => child.text()).join("\n"); }
}

export async function loadHelp(feature) {
  const entrypoint = new URL(`${feature}/web/${feature}.js`, directory);
  let extension;
  const listeners = {};
  const document = {
    body: new Element(), head: new Element(),
    createElement: () => new Element(), getElementById: () => null,
  };
  const context = vm.createContext({
    document, window: { location: { hostname: "localhost" } }, console, URL,
    fetch: async (url) => ({ ok: true, json: async () => JSON.parse(await readFile(url, "utf8")) }),
  });
  const source = await readFile(entrypoint, "utf8");
  const module = new vm.SourceTextModule(source, {
    context, initializeImportMeta(meta) { meta.url = entrypoint.href; },
  });
  await module.link((name) => {
    const key = name.endsWith("app.js") ? "app" : "api";
    const value = key === "app"
      ? { registerExtension(value) { extension = value; } }
      : { addEventListener(name, listener) { listeners[name] = listener; } };
    return new vm.SyntheticModule([key], function () { this.setExport(key, value); }, { context });
  });
  await module.evaluate();
  await extension.init?.();
  return { extension, listeners, document };
}

