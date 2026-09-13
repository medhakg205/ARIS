const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let pythonProcess = null;

function startPythonBackend() {
  const pythonPath = 'python';
  const projectRoot = path.join(__dirname, '..', '..');
  
  console.log(`[ARIS Electron] Starting Python Backend: python -m backend.api.app in ${projectRoot}`);
  pythonProcess = spawn(pythonPath, ['-m', 'backend.api.app'], {
    cwd: projectRoot,
    stdio: 'inherit'
  });

  pythonProcess.on('error', (err) => {
    console.error('[ARIS Electron] Failed to launch Python backend:', err);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#0a0d14',
    title: 'ARIS Studio - Multi-MCU Runtime Intelligence & AI Optimization Platform',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false // allow local API calls to http://127.0.0.1:8765
    },
    autoHideMenuBar: true
  });

  // Always load built dist/index.html
  const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
  console.log(`[ARIS Electron] Loading GUI from: ${indexPath}`);
  mainWindow.loadFile(indexPath);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
