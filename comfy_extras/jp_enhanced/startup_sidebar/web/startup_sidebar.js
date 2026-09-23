import { app } from "/scripts/app.js";

app.registerExtension({
  name: "JPEnhanced.StartupSidebar",
  async setup() {
    await app.extensionManager.setting.set("Comfy.Sidebar.Location", "left");
    app.extensionManager.sidebarTab.activeSidebarTabId = "workflows";
  },
});
