chrome.commands.onCommand.addListener(async (command) => {
  if (command !== "toggle-editor") return;
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) chrome.tabs.sendMessage(tab.id, { type: "PROTO_TOGGLE" }).catch(() => {});
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "PROTO_DOWNLOAD") return;
  const url = `data:text/html;charset=utf-8,${encodeURIComponent(message.html)}`;
  chrome.downloads.download({ url, filename: message.filename, saveAs: true });
  sendResponse({ ok: true });
});
