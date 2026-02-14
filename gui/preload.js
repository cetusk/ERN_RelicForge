const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  findSaveFiles: () => ipcRenderer.invoke('find-save-files'),
  autoLoadSave: (bakPath) => ipcRenderer.invoke('auto-load-save', bakPath),
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  readFileBuffer: (filePath) => ipcRenderer.invoke('read-file-buffer', filePath),
  loadItemsData: () => ipcRenderer.invoke('load-items-data'),
  loadEffectsData: () => ipcRenderer.invoke('load-effects-data'),
  loadStackingData: () => ipcRenderer.invoke('load-stacking-data'),
  loadVesselsData: () => ipcRenderer.invoke('load-vessels-data'),
  savePresetDialog: (jsonStr) => ipcRenderer.invoke('save-preset-dialog', jsonStr),
  loadPresetDialog: () => ipcRenderer.invoke('load-preset-dialog'),
});
