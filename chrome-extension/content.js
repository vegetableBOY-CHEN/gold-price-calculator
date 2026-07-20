(() => {
  if (window.__prototypeCanvasLoaded) return;
  window.__prototypeCanvasLoaded = true;

  const state = { enabled: false, selected: null, history: [], future: [], dragging: null, resizing: null, clipboard: null, changes: new Map() };
  const ROOT_ID = "proto-editor-root";
  let root;
  let outline;
  let panel;

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[c]);
  const selectorFor = (el) => {
    if (el === document.body) return "body";
    if (el === document.documentElement) return "html";
    if (el.id) return `#${CSS.escape(el.id)}`;
    const parts = [];
    while (el && el !== document.body && parts.length < 5) {
      let part = el.tagName.toLowerCase();
      const parent = el.parentElement;
      if (parent) {
        const same = [...parent.children].filter((x) => x.tagName === el.tagName);
        if (same.length > 1) part += `:nth-of-type(${same.indexOf(el) + 1})`;
      }
      parts.unshift(part);
      el = parent;
    }
    return `body > ${parts.join(" > ")}`;
  };
  const snapshot = (el) => {
    const created = el.dataset.protoCreated === "true";
    return {
      selector: selectorFor(el),
      style: el.getAttribute("style"),
      html: el.innerHTML,
      hidden: el.classList.contains("pe-hidden"),
      created,
      outerHTML: created ? el.outerHTML : undefined,
      parentSelector: created && el.parentElement ? selectorFor(el.parentElement) : undefined,
      previousSelector: created && el.previousElementSibling ? selectorFor(el.previousElementSibling) : undefined
    };
  };
  const restore = (snap, shouldSelect = true) => {
    let el = document.querySelector(snap.selector);
    if (!el && snap.created && snap.outerHTML) {
      const template = document.createElement("template");
      template.innerHTML = snap.outerHTML.trim();
      el = template.content.firstElementChild;
      const parent = snap.parentSelector ? document.querySelector(snap.parentSelector) : document.body;
      const previous = snap.previousSelector ? document.querySelector(snap.previousSelector) : null;
      if (previous?.parentElement === parent) previous.insertAdjacentElement("afterend", el);
      else (parent || document.body).prepend(el);
    }
    if (!el) return;
    snap.style == null ? el.removeAttribute("style") : el.setAttribute("style", snap.style);
    el.innerHTML = snap.html;
    el.classList.toggle("pe-hidden", snap.hidden);
    if (shouldSelect) { persist(el); select(el); }
  };
  const checkpoint = (el) => { state.history.push(snapshot(el)); state.future.length = 0; if (state.history.length > 80) state.history.shift(); };
  const persist = (el) => {
    state.changes.set(selectorFor(el), snapshot(el));
    saveChanges();
  };
  const saveChanges = () => chrome.storage.local.set({ [`proto:${location.href}`]: [...state.changes.values()] });
  const directText = (el) => [...el.childNodes].filter((node) => node.nodeType === Node.TEXT_NODE).map((node) => node.textContent).join("").trim();
  const setDirectText = (el, value) => {
    const textNodes = [...el.childNodes].filter((node) => node.nodeType === Node.TEXT_NODE);
    if (!el.children.length) { el.textContent = value; return; }
    if (textNodes.length) {
      textNodes[0].textContent = value;
      textNodes.slice(1).forEach((node) => node.remove());
    } else el.prepend(document.createTextNode(value));
  };
  const toast = (message) => {
    const node = document.createElement("div"); node.className = "pe-toast"; node.textContent = message; root.append(node);
    setTimeout(() => node.remove(), 1500);
  };

  function mount() {
    root = document.createElement("div"); root.id = ROOT_ID;
    root.innerHTML = `
      <div class="pe-toolbar">
        <span class="pe-logo">◈ 原型画布</span><span class="pe-sep"></span>
        <button class="pe-btn active" data-action="select" title="选择元素 (V)">↖ 选择</button>
        <button class="pe-btn" data-action="text" title="编辑文本 (T)">T 文本</button>
        <button class="pe-btn" data-action="insert" title="插入新元素">＋ 插入</button>
        <button class="pe-btn" data-action="copy" title="复制元素 Ctrl+C">⧉ 复制</button>
        <button class="pe-btn" data-action="paste" title="粘贴元素 Ctrl+V">▣ 粘贴</button>
        <span class="pe-sep"></span>
        <button class="pe-btn" data-action="undo" title="撤销 Ctrl+Z">↶</button>
        <button class="pe-btn" data-action="redo" title="重做 Ctrl+Shift+Z">↷</button>
        <button class="pe-btn" data-action="hide" title="隐藏元素">◌ 隐藏</button>
        <button class="pe-btn danger" data-action="delete" title="删除元素">⌫</button>
        <span class="pe-sep"></span>
        <button class="pe-btn" data-action="export" title="导出修改后的 HTML">导出</button>
        <button class="pe-btn" data-action="close" title="关闭编辑器">×</button>
      </div>
      <div class="pe-insert-menu" hidden>
        <button data-insert="text"><b>T</b><span>文字</span></button>
        <button data-insert="button"><b>▣</b><span>按钮</span></button>
        <button data-insert="image"><b>▧</b><span>图片</span></button>
        <button data-insert="container"><b>□</b><span>容器</span></button>
      </div>
      <div class="pe-outline"><span class="pe-label"></span><span class="pe-resize-handle" title="拖动缩放"></span></div>
      <aside class="pe-panel" hidden><h3>元素属性</h3><div class="pe-selector"></div><div class="pe-grid"></div><p class="pe-hint">拖动选中元素可调整位置；双击文字可直接编辑。Ctrl/Cmd+C、V 可复制粘贴元素，方向键可微调。</p></aside>`;
    document.documentElement.append(root);
    outline = root.querySelector(".pe-outline"); panel = root.querySelector(".pe-panel");
    root.addEventListener("click", toolbarClick);
    root.querySelector(".pe-resize-handle").addEventListener("pointerdown", startResize);
  }

  function toggle() {
    if (!root) mount();
    state.enabled = !state.enabled;
    root.hidden = !state.enabled;
    document.body.classList.toggle("pe-selecting", state.enabled);
    if (!state.enabled) deselect(); else toast("编辑模式已开启 · 点击页面元素开始");
  }
  function deselect() {
    state.selected?.classList.remove("pe-editing");
    state.selected = null;
    if (outline) outline.style.display = "none";
    if (panel) panel.hidden = true;
  }
  function select(el) {
    if (!el || el === root || root.contains(el)) return;
    const insertMenu = root?.querySelector(".pe-insert-menu");
    if (insertMenu) insertMenu.hidden = true;
    state.selected?.classList.remove("pe-editing"); state.selected = el;
    updateOutline(); renderPanel();
  }
  function updateOutline() {
    if (!outline) return;
    if (!state.selected?.isConnected) return deselect();
    const r = state.selected.getBoundingClientRect();
    Object.assign(outline.style, { display: "block", left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px` });
    outline.querySelector(".pe-label").textContent = `${state.selected.tagName.toLowerCase()} · ${Math.round(r.width)}×${Math.round(r.height)}`;
  }
  function renderPanel() {
    const el = state.selected; if (!el) return;
    const cs = getComputedStyle(el); panel.hidden = false;
    panel.querySelector(".pe-selector").textContent = selectorFor(el);
    panel.querySelector(".pe-grid").innerHTML = `
      <div class="pe-field wide"><label>${el.children.length ? "直属文字（保留内部元素）" : "文字内容"}</label><textarea data-prop="text">${escapeHtml(el.children.length ? directText(el) : el.textContent || "")}</textarea></div>
      ${el instanceof HTMLImageElement ? `<div class="pe-field wide"><label>图片地址</label><input data-attr="src" value="${escapeHtml(el.getAttribute("src") || "")}"></div>` : ""}
      ${el instanceof HTMLAnchorElement ? `<div class="pe-field wide"><label>链接地址</label><input data-attr="href" value="${escapeHtml(el.getAttribute("href") || "")}"></div>` : ""}
      <div class="pe-field"><label>文字颜色</label><input type="color" data-prop="color" value="${rgbToHex(cs.color)}"></div>
      <div class="pe-field"><label>背景颜色</label><input type="color" data-prop="backgroundColor" value="${rgbToHex(cs.backgroundColor)}"></div>
      <div class="pe-field"><label>字号</label><input data-prop="fontSize" value="${parseFloat(cs.fontSize) || 16}" type="number"></div>
      <div class="pe-field"><label>字重</label><select data-prop="fontWeight"><option>400</option><option>500</option><option>600</option><option>700</option><option>800</option></select></div>
      <div class="pe-field"><label>圆角</label><input data-prop="borderRadius" value="${parseFloat(cs.borderRadius) || 0}" type="number"></div>
      <div class="pe-field"><label>透明度 %</label><input data-prop="opacity" value="${Math.round(parseFloat(cs.opacity) * 100)}" min="0" max="100" type="number"></div>
      <div class="pe-field"><label>宽度 px</label><input data-prop="width" value="${Math.round(el.getBoundingClientRect().width)}" type="number"></div>
      <div class="pe-field"><label>高度 px</label><input data-prop="height" value="${Math.round(el.getBoundingClientRect().height)}" type="number"></div>`;
    panel.querySelector('[data-prop="fontWeight"]').value = ["400","500","600","700","800"].includes(cs.fontWeight) ? cs.fontWeight : "400";
    panel.querySelectorAll("input,textarea,select").forEach((input) => {
      input.addEventListener("focus", () => { input.__before = snapshot(el); });
      input.addEventListener("input", () => applyField(input));
      input.addEventListener("change", () => { if (input.__before) state.history.push(input.__before); state.future.length = 0; persist(el); });
    });
  }
  function applyField(input) {
    const el = state.selected; if (!el) return;
    if (input.dataset.attr) { el.setAttribute(input.dataset.attr, input.value); updateOutline(); return; }
    const prop = input.dataset.prop;
    if (prop === "text") setDirectText(el, input.value);
    else if (prop === "opacity") el.style.opacity = Number(input.value) / 100;
    else if (["fontSize","borderRadius","width","height"].includes(prop)) el.style[prop] = `${input.value}px`;
    else el.style[prop] = input.value;
    updateOutline();
  }
  function rgbToHex(rgb) {
    const nums = rgb.match(/[\d.]+/g); if (!nums || nums.length < 3 || (nums[3] !== undefined && Number(nums[3]) === 0)) return "#ffffff";
    return `#${nums.slice(0,3).map((n) => Number(n).toString(16).padStart(2,"0")).join("")}`;
  }

  function toolbarClick(e) {
    const insertType = e.target.closest("[data-insert]")?.dataset.insert;
    if (insertType) { root.querySelector(".pe-insert-menu").hidden = true; return insertElement(insertType); }
    const action = e.target.closest("[data-action]")?.dataset.action; if (!action) return;
    if (action === "close") return toggle();
    if (action === "undo") return undo();
    if (action === "redo") return redo();
    if (action === "export") return exportHtml();
    if (action === "insert") { const menu = root.querySelector(".pe-insert-menu"); menu.hidden = !menu.hidden; return; }
    if (action === "copy") return copySelected();
    if (action === "paste") return pasteCopied();
    if (!state.selected) return toast("请先选择一个元素");
    if (action === "text") return beginTextEdit(state.selected);
    if (action === "hide") { checkpoint(state.selected); state.selected.classList.toggle("pe-hidden"); persist(state.selected); return; }
    if (action === "delete") { checkpoint(state.selected); state.selected.style.display = "none"; persist(state.selected); deselect(); }
  }
  function nextCreatedId() {
    let id;
    do { id = `proto-element-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`; } while (document.getElementById(id));
    return id;
  }
  function addCreatedElement(el) {
    if (!el.id || document.getElementById(el.id)) el.id = nextCreatedId();
    el.dataset.protoCreated = "true";
    const anchor = state.selected;
    if (anchor?.parentElement && !root.contains(anchor)) anchor.insertAdjacentElement("afterend", el);
    else document.body.append(el);
    const snap = snapshot(el);
    state.history.push({ kind: "insert", snap });
    state.future.length = 0;
    persist(el);
    select(el);
    toast("已插入新元素");
  }
  function insertElement(type) {
    let el;
    if (type === "text") {
      el = document.createElement("div"); el.textContent = "双击编辑这段文字";
      el.style.cssText = "display:block;margin:12px 0;color:#202124;font:500 20px/1.5 system-ui,sans-serif;";
    } else if (type === "button") {
      el = document.createElement("button"); el.textContent = "按钮"; el.type = "button";
      el.style.cssText = "display:inline-flex;align-items:center;justify-content:center;margin:12px 0;padding:10px 18px;border:0;border-radius:8px;color:#17140a;background:#f5c84c;font:600 14px/1 system-ui,sans-serif;cursor:pointer;";
    } else if (type === "image") {
      el = document.createElement("img"); el.alt = "图片占位";
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270"><rect width="100%" height="100%" fill="#e8e8ec"/><path d="M0 230l130-120 85 76 70-62 195 146H0z" fill="#c5c5cc"/><circle cx="380" cy="70" r="28" fill="#c5c5cc"/><text x="240" y="145" text-anchor="middle" fill="#777780" font-family="sans-serif" font-size="20">图片占位</text></svg>`;
      el.src = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
      el.style.cssText = "display:block;width:480px;max-width:100%;height:auto;margin:12px 0;border-radius:10px;";
    } else {
      el = document.createElement("div"); el.textContent = "容器";
      el.style.cssText = "display:block;min-height:120px;margin:12px 0;padding:20px;border:2px dashed #b9b9c2;border-radius:10px;color:#777780;background:#f7f7f9;font:500 14px/1.5 system-ui,sans-serif;";
    }
    addCreatedElement(el);
  }
  function copySelected() {
    if (!state.selected) return toast("请先选择要复制的元素");
    state.clipboard = cloneWithComputedStyles(state.selected);
    const count = state.selected.querySelectorAll("*").length + 1;
    toast(`已完整复制 ${count} 个节点及其样式`);
  }
  function cloneWithComputedStyles(source) {
    const clone = source.cloneNode(true);
    const sources = [source, ...source.querySelectorAll("*")];
    const targets = [clone, ...clone.querySelectorAll("*")];
    sources.forEach((sourceNode, index) => {
      const targetNode = targets[index];
      if (!targetNode?.style) return;
      const computed = getComputedStyle(sourceNode);
      targetNode.style.cssText = "";
      for (let propertyIndex = 0; propertyIndex < computed.length; propertyIndex += 1) {
        const property = computed[propertyIndex];
        try { targetNode.style.setProperty(property, computed.getPropertyValue(property), computed.getPropertyPriority(property)); } catch (_) {}
      }
      targetNode.classList.remove("pe-editing", "pe-hidden");
      targetNode.removeAttribute("contenteditable");
      targetNode.removeAttribute("data-proto-created");
      if (sourceNode instanceof HTMLInputElement && targetNode instanceof HTMLInputElement) {
        targetNode.value = sourceNode.value; targetNode.setAttribute("value", sourceNode.value);
        targetNode.checked = sourceNode.checked; targetNode.toggleAttribute("checked", sourceNode.checked);
      }
      if (sourceNode instanceof HTMLTextAreaElement && targetNode instanceof HTMLTextAreaElement) {
        targetNode.value = sourceNode.value; targetNode.textContent = sourceNode.value;
      }
      if (sourceNode instanceof HTMLSelectElement && targetNode instanceof HTMLSelectElement) {
        targetNode.value = sourceNode.value;
        [...targetNode.options].forEach((option) => option.toggleAttribute("selected", option.value === sourceNode.value));
      }
    });
    return clone;
  }
  function pasteCopied() {
    if (!state.clipboard) return toast("还没有复制元素");
    const clone = state.clipboard.cloneNode(true);
    clone.querySelectorAll("[data-proto-created]").forEach((node) => node.removeAttribute("data-proto-created"));
    remapCloneIds(clone);
    const left = parseFloat(clone.style.left) || 0, top = parseFloat(clone.style.top) || 0;
    if (!clone.style.position || clone.style.position === "static") clone.style.position = "relative";
    clone.style.left = `${left + 12}px`; clone.style.top = `${top + 12}px`;
    addCreatedElement(clone);
    toast("已粘贴元素");
  }
  function remapCloneIds(clone) {
    const idMap = new Map();
    const nodes = [clone, ...clone.querySelectorAll("[id]")];
    nodes.forEach((node) => {
      if (!node.id) return;
      const replacement = nextCreatedId().replace("proto-element", "proto-child");
      idMap.set(node.id, replacement); node.id = replacement;
    });
    const tokenAttributes = ["for", "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "list"];
    [clone, ...clone.querySelectorAll("*")].forEach((node) => {
      tokenAttributes.forEach((attribute) => {
        if (!node.hasAttribute(attribute)) return;
        const rewritten = node.getAttribute(attribute).split(/\s+/).map((token) => idMap.get(token) || token).join(" ");
        node.setAttribute(attribute, rewritten);
      });
      const href = node.getAttribute("href");
      if (href?.startsWith("#") && idMap.has(href.slice(1))) node.setAttribute("href", `#${idMap.get(href.slice(1))}`);
    });
  }
  function startResize(e) {
    if (!state.selected) return;
    e.preventDefault(); e.stopPropagation();
    const rect = state.selected.getBoundingClientRect();
    state.resizing = { el: state.selected, x: e.clientX, y: e.clientY, width: rect.width, height: rect.height, moved: false };
    e.currentTarget.setPointerCapture?.(e.pointerId);
  }
  function beginTextEdit(el) {
    checkpoint(el); el.contentEditable = "true"; el.classList.add("pe-editing"); el.focus();
    const done = () => { el.removeAttribute("contenteditable"); el.classList.remove("pe-editing"); persist(el); renderPanel(); };
    el.addEventListener("blur", done, { once: true });
  }
  function undo() {
    const snap = state.history.pop(); if (!snap) return toast("没有可撤销的操作");
    if (snap.kind === "insert") {
      document.querySelector(snap.snap.selector)?.remove();
      state.changes.delete(snap.snap.selector); saveChanges(); state.future.push(snap); deselect();
      return;
    }
    const current = document.querySelector(snap.selector); if (current) state.future.push(snapshot(current)); restore(snap);
  }
  function redo() {
    const snap = state.future.pop(); if (!snap) return toast("没有可重做的操作");
    if (snap.kind === "insert") { state.history.push(snap); restore(snap.snap); return; }
    const current = document.querySelector(snap.selector); if (current) state.history.push(snapshot(current)); restore(snap);
  }
  function exportHtml() {
    const clone = document.documentElement.cloneNode(true); clone.querySelector(`#${ROOT_ID}`)?.remove();
    clone.querySelectorAll(".pe-editing,.pe-hidden").forEach((el) => { el.classList.remove("pe-editing"); if (el.classList.contains("pe-hidden")) el.style.display = "none"; el.classList.remove("pe-hidden"); });
    clone.querySelectorAll("[data-proto-created]").forEach((el) => el.removeAttribute("data-proto-created"));
    const html = `<!doctype html>\n${clone.outerHTML}`;
    const filename = `${(document.title || "prototype").replace(/[\\/:*?\"<>|]/g, "-")}-prototype.html`;
    chrome.runtime.sendMessage({ type: "PROTO_DOWNLOAD", html, filename }); toast("正在导出 HTML");
  }

  document.addEventListener("pointerdown", (e) => {
    if (!state.enabled || root?.contains(e.target)) return;
    e.preventDefault(); e.stopPropagation();
    const wasSelected = state.selected === e.target;
    select(e.target);
    if (!wasSelected) return;
    const cs = getComputedStyle(e.target);
    state.dragging = {
      el: e.target, x: e.clientX, y: e.clientY,
      left: parseFloat(cs.left) || 0, top: parseFloat(cs.top) || 0,
      originalPosition: cs.position, moved: false
    };
  }, true);
  document.addEventListener("pointermove", (e) => {
    if (state.resizing) {
      if (!state.resizing.moved) { checkpoint(state.resizing.el); state.resizing.moved = true; }
      const width = Math.max(16, state.resizing.width + e.clientX - state.resizing.x);
      const height = Math.max(16, state.resizing.height + e.clientY - state.resizing.y);
      state.resizing.el.style.width = `${Math.round(width)}px`;
      state.resizing.el.style.height = `${Math.round(height)}px`;
      updateOutline(); return;
    }
    if (!state.dragging) return;
    const dx = e.clientX - state.dragging.x, dy = e.clientY - state.dragging.y;
    if (!state.dragging.moved && Math.abs(dx) + Math.abs(dy) < 4) return;
    if (!state.dragging.moved) {
      checkpoint(state.dragging.el);
      state.dragging.moved = true;
      if (state.dragging.originalPosition === "static") state.dragging.el.style.position = "relative";
    }
    state.dragging.el.style.left = `${state.dragging.left + dx}px`; state.dragging.el.style.top = `${state.dragging.top + dy}px`; updateOutline();
  }, true);
  document.addEventListener("pointerup", () => {
    if (state.resizing) {
      if (state.resizing.moved) { persist(state.resizing.el); renderPanel(); }
      state.resizing = null;
    }
    if (!state.dragging) return;
    if (state.dragging.moved) { persist(state.dragging.el); renderPanel(); }
    state.dragging = null;
  }, true);
  document.addEventListener("click", (e) => {
    if (state.enabled && !root?.contains(e.target)) { e.preventDefault(); e.stopPropagation(); }
  }, true);
  document.addEventListener("dblclick", (e) => { if (state.enabled && !root.contains(e.target)) { e.preventDefault(); beginTextEdit(e.target); } }, true);
  document.addEventListener("keydown", (e) => {
    if (!state.enabled) return;
    const typing = /input|textarea|select/i.test(e.target.tagName) || e.target.isContentEditable;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); return e.shiftKey ? redo() : undo(); }
    if (!typing && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") { e.preventDefault(); return copySelected(); }
    if (!typing && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "v") { e.preventDefault(); return pasteCopied(); }
    if (!state.selected || typing) return;
    if (["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"].includes(e.key)) {
      e.preventDefault(); checkpoint(state.selected); const step = e.shiftKey ? 10 : 1; const cs = getComputedStyle(state.selected);
      if (cs.position === "static") state.selected.style.position = "relative";
      const axis = /Left|Right/.test(e.key) ? "left" : "top"; const sign = /Right|Down/.test(e.key) ? 1 : -1;
      state.selected.style[axis] = `${(parseFloat(cs[axis]) || 0) + sign * step}px`; persist(state.selected); updateOutline();
    }
    if (e.key === "Delete") { checkpoint(state.selected); state.selected.style.display = "none"; persist(state.selected); deselect(); }
    if (e.key === "Escape") deselect();
  }, true);
  window.addEventListener("scroll", updateOutline, true); window.addEventListener("resize", updateOutline);
  chrome.runtime.onMessage.addListener((message) => { if (message?.type === "PROTO_TOGGLE") toggle(); });
  chrome.storage.local.get(`proto:${location.href}`, (data) => {
    const saved = data[`proto:${location.href}`] || [];
    saved.forEach((snap) => { state.changes.set(snap.selector, snap); restore(snap, false); });
  });
})();
