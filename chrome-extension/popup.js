const button = document.querySelector("#toggle");
const status = document.querySelector("#status");

button.addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !/^https?:/.test(tab.url || "")) {
    status.textContent = "此页面受 Chrome 保护，无法编辑。";
    return;
  }
  chrome.tabs.sendMessage(tab.id, { type: "PROTO_TOGGLE" }, () => {
    if (chrome.runtime.lastError) status.textContent = "请刷新页面后重试。";
    else window.close();
  });
});
