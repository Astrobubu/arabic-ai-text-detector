const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  exportPdf: (defaultName) => ipcRenderer.invoke('export-pdf', defaultName),
  onBackendReady: (callback) => ipcRenderer.on('backend-ready', (_event, payload) => callback(payload)),
  onBackendError: (callback) => ipcRenderer.on('backend-error', (_event, payload) => callback(payload)),
});
