const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const os = require('os');

let mainWindow;

// Resource directory: packaged vs dev
const resourcesDir = app.isPackaged
  ? path.join(process.resourcesPath, 'resources')
  : path.resolve(__dirname, '..', 'resources');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'ERN RelicForge',
    backgroundColor: '#1a1a1a',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// ---- IPC Handlers ----

ipcMain.handle('save-preset-dialog', async (_event, jsonStr) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: 'プリセットを保存',
    defaultPath: 'preset.json',
    filters: [
      { name: 'JSON Files', extensions: ['json'] },
    ],
  });
  if (result.canceled || !result.filePath) return null;
  fs.writeFileSync(result.filePath, jsonStr, 'utf-8');
  return result.filePath;
});

ipcMain.handle('load-preset-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'プリセットを読み込み',
    filters: [
      { name: 'JSON Files', extensions: ['json'] },
    ],
    properties: ['openFile'],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  const raw = fs.readFileSync(result.filePaths[0], 'utf-8');
  return JSON.parse(raw);
});

// ---- Auto-load: find Nightreign save files ----
ipcMain.handle('find-save-files', async () => {
  try {
    const nightreignDir = path.join(
      os.homedir(), 'AppData', 'Roaming', 'Nightreign');
    if (!fs.existsSync(nightreignDir)) return [];

    const entries = fs.readdirSync(nightreignDir, { withFileTypes: true });
    const results = [];
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const bakPath = path.join(nightreignDir, entry.name, 'NR0000.sl2.bak');
      if (fs.existsSync(bakPath)) {
        const stat = fs.statSync(bakPath);
        results.push({
          id: entry.name,
          path: bakPath,
          mtime: stat.mtime.toISOString(),
        });
      }
    }
    // Sort by mtime descending (newest first)
    results.sort((a, b) => b.mtime.localeCompare(a.mtime));
    return results;
  } catch (err) {
    console.error('find-save-files error:', err);
    return [];
  }
});

ipcMain.handle('auto-load-save', async (_event, bakPath) => {
  const tmpDir = os.tmpdir();
  const dest = path.join(tmpDir, 'ern_relicforge_NR0000.sl2');
  fs.copyFileSync(bakPath, dest);
  return dest;
});

ipcMain.handle('open-file-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'セーブファイルを選択',
    filters: [
      { name: 'SL2 Save Files', extensions: ['sl2'] },
      { name: 'All Files', extensions: ['*'] },
    ],
    properties: ['openFile'],
  });
  if (result.canceled || result.filePaths.length === 0) return null;
  return result.filePaths[0];
});

// ---- File reading (for JS parser in renderer) ----
ipcMain.handle('read-file-buffer', async (_event, filePath) => {
  return fs.readFileSync(filePath);
});

// ---- Resource data loading ----
ipcMain.handle('load-items-data', async () => {
  const raw = fs.readFileSync(path.join(resourcesDir, 'items_data.json'), 'utf-8');
  return JSON.parse(raw);
});

ipcMain.handle('load-effects-data', async () => {
  const raw = fs.readFileSync(path.join(resourcesDir, 'effects_data.json'), 'utf-8');
  return JSON.parse(raw);
});

ipcMain.handle('load-stacking-data', async () => {
  const effectsFile = path.join(resourcesDir, 'effects_data.json');
  try {
    const raw = fs.readFileSync(effectsFile, 'utf-8');
    const data = JSON.parse(raw);
    // Build lookup: effectId (string) -> { stackable, stackNotes, key, name_ja, name_en, deepOnly }
    const lookup = {};
    for (const [id, entry] of Object.entries(data.effects || {})) {
      lookup[id] = {
        stackable: entry.stackable,
        stackNotes: entry.stackNotes || '',
        key: entry.key || '',
        name_ja: entry.name_ja || '',
        name_en: entry.name_en || '',
        deepOnly: entry.deepOnly || false,
      };
    }
    return lookup;
  } catch (e) {
    console.error('Failed to load stacking data:', e.message);
    return {};
  }
});

ipcMain.handle('load-vessels-data', async () => {
  const vesselsFile = path.join(resourcesDir, 'vessels_data.json');
  try {
    const raw = fs.readFileSync(vesselsFile, 'utf-8');
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to load vessels data:', e.message);
    return null;
  }
});
