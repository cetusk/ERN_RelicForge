const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { execFile, spawn } = require('child_process');
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

ipcMain.handle('load-stacking-data', async () => {
  const projectRoot = path.resolve(__dirname, '..');
  const effectsFile = path.join(projectRoot, 'resources', 'effects_data.json');
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
  const projectRoot = path.resolve(__dirname, '..');
  const vesselsFile = path.join(projectRoot, 'resources', 'vessels_data.json');
  try {
    const raw = fs.readFileSync(vesselsFile, 'utf-8');
    return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to load vessels data:', e.message);
    return null;
  }
});

ipcMain.handle('run-optimizer', async (_event, params) => {
  const projectRoot = path.resolve(__dirname, '..');
  const optimizerScript = path.join(projectRoot, 'src', 'relic_optimizer.py');

  // Write relic data to temp file
  const tmpInput = path.join(os.tmpdir(), `relicforge_opt_input_${Date.now()}.json`);
  const tmpEffects = path.join(os.tmpdir(), `relicforge_opt_effects_${Date.now()}.json`);
  const tmpOutput = path.join(os.tmpdir(), `relicforge_opt_output_${Date.now()}.json`);

  const cleanup = () => {
    [tmpInput, tmpEffects, tmpOutput].forEach(f => {
      try { fs.unlinkSync(f); } catch (_) {}
    });
  };

  try {
    // Write input relic data
    fs.writeFileSync(tmpInput, JSON.stringify(params.relicData, null, 0), 'utf-8');

    // Write effects config
    const effectsConfig = { effects: params.effects || [] };
    fs.writeFileSync(tmpEffects, JSON.stringify(effectsConfig, null, 0), 'utf-8');

    // Build args
    const pyArgs = [
      optimizerScript,
      '--input', tmpInput,
      '--effects', tmpEffects,
      '-o', tmpOutput,
      '--top', String(params.top || 50),
      '--candidates', String(params.candidates || 30),
    ];
    if (params.character) {
      pyArgs.push('--character', params.character);
    }
    if (params.vessel) {
      pyArgs.push('--vessel', params.vessel);
    }
    if (params.combined) {
      pyArgs.push('--combined');
    } else {
      // Normal mode: include UniqueRelic (goes into normal slots)
      pyArgs.push('--types', 'Relic,UniqueRelic');
    }

    return new Promise((resolve, reject) => {
      const tryRun = (cmd) => {
        const proc = spawn(cmd, pyArgs, { timeout: 120000, shell: true });
        let stderrBuf = '';

        proc.stderr.on('data', (chunk) => {
          const text = chunk.toString();
          stderrBuf += text;
          // Parse PROGRESS lines and send to renderer
          const lines = text.split('\n');
          for (const line of lines) {
            const m = line.match(/^PROGRESS:(\d+)\/(\d+)/);
            if (m) {
              mainWindow.webContents.send('optimizer-progress', {
                current: parseInt(m[1]),
                total: parseInt(m[2]),
              });
            }
          }
        });

        proc.on('error', (err) => {
          if (cmd === 'python3') {
            tryRun('python');
            return;
          }
          cleanup();
          reject(`Optimizer error: ${err.message}`);
        });

        proc.on('close', (code) => {
          if (code !== 0) {
            // Fallback: python3 not found (9009=Windows, 127=Unix)
            if (cmd === 'python3' && (code === 9009 || code === 127 ||
                stderrBuf.includes('not found') || stderrBuf.includes('not recognized'))) {
              tryRun('python');
              return;
            }
            cleanup();
            reject(`Optimizer exited with code ${code}\n${stderrBuf}`);
            return;
          }
          try {
            const data = fs.readFileSync(tmpOutput, 'utf-8');
            cleanup();
            resolve(JSON.parse(data));
          } catch (e) {
            cleanup();
            reject(`Failed to read optimizer output: ${e.message}`);
          }
        });
      };
      tryRun('python3');
    });
  } catch (e) {
    cleanup();
    throw `Optimizer setup error: ${e.message}`;
  }
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
