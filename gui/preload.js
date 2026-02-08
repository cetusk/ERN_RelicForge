const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  openFileDialog: () => ipcRenderer.invoke('open-file-dialog'),
  parseSaveFile: (filePath) => ipcRenderer.invoke('parse-save-file', filePath),
});
