const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  parseSaveFile: (filePath) => ipcRenderer.invoke('parse-save-file', filePath),
  loadStackingData: () => ipcRenderer.invoke('load-stacking-data'),
  loadVesselsData: () => ipcRenderer.invoke('load-vessels-data'),
  runOptimizer: (params) => ipcRenderer.invoke('run-optimizer', params),
  savePresetDialog: (jsonStr) => ipcRenderer.invoke('save-preset-dialog', jsonStr),
  loadPresetDialog: () => ipcRenderer.invoke('load-preset-dialog'),
});
