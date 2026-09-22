const { app, BrowserWindow } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow = null;
let pythonProcess = null;

function checkBackendHealth() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:8765/api/health', (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => {
      resolve(false);
    });
    req.setTimeout(800, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function waitForBackend(timeoutMs = 12000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const alive = await checkBackendHealth();
    if (alive) {
      console.log('[ARIS Electron] Backend server is responsive on port 8765.');
      return true;
    }
    await new Promise((r) => setTimeout(r, 400));
  }
  console.warn('[ARIS Electron] Backend did not respond within timeout.');
  return false;
}

function startPythonBackend() {
  const projectRoot = path.join(__dirname, '..', '..');
  console.log(`[ARIS Electron] Launching Python backend: python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8765 in ${projectRoot}`);
  
  pythonProcess = spawn('python', ['-m', 'uvicorn', 'backend.api.app:app', '--host', '127.0.0.1', '--port', '8765'], {
    cwd: projectRoot,
    stdio: 'inherit',
    shell: true
  });

  pythonProcess.on('error', (err) => {
    console.error('[ARIS Electron] Failed to launch Python backend process:', err);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#12151a',
    title: 'ARIS Studio - Multi-MCU Runtime Intelligence & AI Optimization Platform',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false // allow local API calls to http://127.0.0.1:8765
    },
    autoHideMenuBar: true
  });

  const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
  console.log(`[ARIS Electron] Loading GUI from: ${indexPath}`);
  mainWindow.loadFile(indexPath);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  const alreadyRunning = await checkBackendHealth();
  if (alreadyRunning) {
    console.log('[ARIS Electron] Existing backend instance detected on port 8765.');
  } else {
    startPythonBackend();
    await waitForBackend();
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (_) {}
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

