"use strict";

(() => {
  const root = document.documentElement;
  const storage = {
    get(key, fallback) { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Preferência apenas nesta sessão. */ } }
  };
  const setTheme = (theme) => {
    if (!["dark", "light", "contrast"].includes(theme)) theme = "dark";
    root.dataset.theme = theme;
    document.querySelectorAll("[data-theme-choice]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme));
    });
    storage.set("siled-theme", theme);
  };
  setTheme(storage.get("siled-theme", "dark"));
  document.querySelectorAll("[data-theme-choice]").forEach(button => {
    button.addEventListener("click", () => setTheme(button.dataset.themeChoice));
  });

  let fontSize = Math.max(14, Math.min(20, Number(storage.get("siled-font-size", "14")) || 14));
  const applyFont = () => { root.style.setProperty("--font-size", `${fontSize}px`); storage.set("siled-font-size", String(fontSize)); };
  applyFont();
  document.querySelectorAll("[data-font]").forEach(button => button.addEventListener("click", () => {
    fontSize = button.dataset.font === "reset" ? 14 : Math.max(14, Math.min(20, fontSize + (button.dataset.font === "increase" ? 2 : -2)));
    applyFont();
  }));
  const motion = document.getElementById("reduce-motion");
  const reduced = storage.get("siled-motion", "normal") === "reduced";
  root.dataset.motion = reduced ? "reduced" : "normal";
  if (motion) {
    motion.checked = reduced;
    motion.addEventListener("change", () => {
      root.dataset.motion = motion.checked ? "reduced" : "normal";
      storage.set("siled-motion", root.dataset.motion);
    });
  }

  const overlay = document.getElementById("drawer-overlay");
  const main = document.querySelector(".dashboard-shell");
  let activeDrawer = null;
  let opener = null;
  const closePanel = () => {
    if (!activeDrawer) return;
    activeDrawer.hidden = true;
    if (overlay) overlay.hidden = true;
    if (main) main.inert = false;
    opener?.setAttribute("aria-expanded", "false");
    opener?.focus();
    activeDrawer = null;
  };
  document.querySelectorAll("[data-panel]").forEach(button => button.addEventListener("click", () => {
    closePanel();
    const panel = document.getElementById(button.dataset.panel);
    if (!panel) return;
    opener = button;
    activeDrawer = panel;
    panel.hidden = false;
    if (overlay) overlay.hidden = false;
    if (main) main.inert = true;
    button.setAttribute("aria-expanded", "true");
    panel.querySelector("button,a,input")?.focus();
  }));
  document.querySelectorAll("[data-close-panel]").forEach(button => button.addEventListener("click", closePanel));
  overlay?.addEventListener("click", closePanel);
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closePanel();
    if (event.key !== "Tab" || !activeDrawer) return;
    const focusable = [...activeDrawer.querySelectorAll("button,a[href],input,select,[tabindex='0']")].filter(item => !item.disabled && !item.hidden);
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
  });

  const sidebarToggle = document.getElementById("toggle-sidebar");
  sidebarToggle?.addEventListener("click", () => {
    const collapsed = document.querySelector(".workspace-grid").classList.toggle("sidebar-collapsed");
    sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
    sidebarToggle.title = collapsed ? "Abrir barra de acesso" : "Fechar barra de acesso";
    sidebarToggle.querySelector("span").textContent = sidebarToggle.title;
  });
  const files = document.getElementById("arquivos");
  files?.addEventListener("change", () => {
    const total = [...files.files].reduce((sum, file) => sum + file.size, 0);
    const invalid = files.files.length > 10 || total > 25 * 1024 * 1024;
    files.setCustomValidity(invalid ? "Selecione até 10 arquivos e 25 MB por envio." : "");
    document.getElementById("file-selection").textContent = files.files.length
      ? `${files.files.length} arquivo(s) · ${(total / 1024 / 1024).toFixed(2)} MB: ${[...files.files].map(file => file.name).join(", ")}`
      : "Nenhum arquivo selecionado.";
  });
  document.getElementById("print-report")?.addEventListener("click", () => window.print());
})();
