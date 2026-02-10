const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  findSaveFiles: () => ipcRenderer.invoke('find-save-files'),
  autoLoadSave: (bakPath) => ipcRenderer.invoke('auto-load-save', bakPath),
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  parseSaveFile: (filePath) => ipcRenderer.invoke('parse-save-file', filePath),
  loadStackingData: () => ipcRenderer.invoke('load-stacking-data'),
  loadVesselsData: () => ipcRenderer.invoke('load-vessels-data'),
  runOptimizer: (params) => ipcRenderer.invoke('run-optimizer', params),
  onOptimizerProgress: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('optimizer-progress', handler);
    return () => ipcRenderer.removeListener('optimizer-progress', handler);
  },
  savePresetDialog: (jsonStr) => ipcRenderer.invoke('save-preset-dialog', jsonStr),
  loadPresetDialog: () => ipcRenderer.invoke('load-preset-dialog'),
});
