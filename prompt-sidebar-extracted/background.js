// Disable the panel globally — only enable it for the tab the user clicks on
chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setOptions({ enabled: false });
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });
});

// Toggle the panel for the exact tab the icon was clicked on
chrome.action.onClicked.addListener(async (tab) => {
  const { enabled } = await chrome.sidePanel.getOptions({ tabId: tab.id });
  if (enabled) {
    await chrome.sidePanel.setOptions({ tabId: tab.id, enabled: false });
  } else {
    await chrome.sidePanel.setOptions({ tabId: tab.id, enabled: true, path: 'sidebar.html' });
    await chrome.sidePanel.open({ tabId: tab.id });
  }
});
