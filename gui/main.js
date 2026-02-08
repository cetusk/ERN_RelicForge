const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { execFile } = require('child_process');
const fs = require('fs');
const os = require('os');

let mainWindow;

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

ipcMain.handle('parse-save-file', async (_event, sl2Path) => {
  const projectRoot = path.resolve(__dirname, '..');
  const parserScript = path.join(projectRoot, 'src', 'relic_parser.py');
  const itemsFile = path.join(projectRoot, 'resources', 'items_data.json');
  const effectsFile = path.join(projectRoot, 'resources', 'effects_data.json');

  const tmpFile = path.join(os.tmpdir(), `relicforge_${Date.now()}.json`);

  return new Promise((resolve, reject) => {
    const args = [
      parserScript,
      sl2Path,
      '-o', tmpFile,
      '--items', itemsFile,
      '--effects', effectsFile,
    ];

    execFile('python3', args, { timeout: 60000 }, (error, stdout, stderr) => {
      if (error) {
        // Try 'python' if 'python3' is not available (Windows)
        execFile('python', args, { timeout: 60000 }, (error2, stdout2, stderr2) => {
          if (error2) {
            reject(`Parser error: ${error2.message}\n${stderr2 || stderr}`);
            return;
          }
          readAndResolve();
        });
        return;
      }
      readAndResolve();
    });

    function readAndResolve() {
      try {
        const data = fs.readFileSync(tmpFile, 'utf-8');
        fs.unlinkSync(tmpFile);
        resolve(JSON.parse(data));
      } catch (e) {
        reject(`Failed to read parser output: ${e.message}`);
      }
    }
  });
});
