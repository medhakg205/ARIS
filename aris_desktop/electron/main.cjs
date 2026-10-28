const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs');
const { spawn, spawnSync } = require('child_process');

// Set Application Name & Windows AppUserModelId so Taskbar displays 'ARIS'
app.name = 'ARIS';
app.setName('ARIS');
if (process.platform === 'win32') {
  app.setAppUserModelId('ARIS');
}

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const BACKEND_DIR = path.join(PROJECT_ROOT, 'backend');
const LOG_FILE = path.join(BACKEND_DIR, 'backend_supervisor.log');
const PORT = 8765;
const MAX_RESTART_ATTEMPTS = 5;

let mainWindow = null;
let pythonProcess = null;
let isShuttingDown = false;
let restartAttempts = 0;
let backendState = 'STARTING'; // 'STARTING' | 'ONLINE' | 'RECOVERING' | 'OFFLINE'
let activePid = null;

// Persistent supervisor logger
function supervisorLog(event, details = {}) {
  const timestamp = new Date().toISOString();
  const entry = {
    timestamp,
    event,
    ...details
  };
  const line = `[${timestamp}] [${event}] ${JSON.stringify(details)}\n`;
  try {
    fs.appendFileSync(LOG_FILE, line, { encoding: 'utf-8' });
  } catch (_) {}
  console.log(`[ARIS Supervisor] [${event}]`, details);
}

// Ensure supervisor log directory exists
try {
  if (!fs.existsSync(BACKEND_DIR)) {
    fs.mkdirSync(BACKEND_DIR, { recursive: true });
  }
} catch (_) {}

supervisorLog('SUPERVISOR_INIT', { projectRoot: PROJECT_ROOT, platform: process.platform });

// Broadcast status to renderer window
function broadcastBackendStatus(state, extra = {}) {
  backendState = state;
  if (mainWindow && !mainWindow.isDestroyed() && mainWindow.webContents) {
    mainWindow.webContents.send('backend-status', {
      state,
      port: PORT,
      pid: activePid,
      ...extra
    });
  }
}

// Probe backend health endpoint
function checkBackendHealth(timeoutMs = 1200) {
  return new Promise((resolve) => {
    const urls = [
      `http://127.0.0.1:${PORT}/health`,
      `http://127.0.0.1:${PORT}/api/health`
    ];

    function tryUrl(idx) {
      if (idx >= urls.length) {
        return resolve(false);
      }
      const req = http.get(urls[idx], (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else {
          tryUrl(idx + 1);
        }
      });
      req.on('error', () => {
        tryUrl(idx + 1);
      });
      req.setTimeout(timeoutMs, () => {
        req.destroy();
        tryUrl(idx + 1);
      });
    }

    tryUrl(0);
  });
}

// Wait with retry/backoff for backend to become responsive
async function waitForBackend(timeoutMs = 20000) {
  const startTime = Date.now();
  let attempt = 0;
  while (Date.now() - startTime < timeoutMs) {
    attempt++;
    const alive = await checkBackendHealth(800);
    if (alive) {
      supervisorLog('HEALTH_PROBE_SUCCESS', { attempt, elapsedMs: Date.now() - startTime });
      return true;
    }
    const delay = Math.min(250 + attempt * 100, 1000);
    await new Promise((r) => setTimeout(r, delay));
  }
  supervisorLog('HEALTH_PROBE_TIMEOUT', { timeoutMs });
  return false;
}

// Robust Python interpreter resolution on Windows
function resolvePythonInterpreter() {
  const candidates = [];

  // 1. Explicit environment override
  if (process.env.PYTHON && fs.existsSync(process.env.PYTHON)) {
    candidates.push(process.env.PYTHON);
  }

  // 2. Active Virtual Environment
  if (process.env.VIRTUAL_ENV) {
    const venvPython = process.platform === 'win32'
      ? path.join(process.env.VIRTUAL_ENV, 'Scripts', 'python.exe')
      : path.join(process.env.VIRTUAL_ENV, 'bin', 'python');
    if (fs.existsSync(venvPython)) candidates.push(venvPython);
  }

  // 3. Local project .venv
  const localVenv = process.platform === 'win32'
    ? path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe')
    : path.join(PROJECT_ROOT, '.venv', 'bin', 'python');
  if (fs.existsSync(localVenv)) candidates.push(localVenv);

  // 4. Known Windows installed Python 3.13 paths
  if (process.platform === 'win32') {
    const userProfile = process.env.USERPROFILE || 'C:\\Users\\aksha';
    const knownPaths = [
      path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python', 'Python313', 'python.exe'),
      path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
      path.join(userProfile, 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
      'C:\\Python313\\python.exe',
      'C:\\Python312\\python.exe'
    ];
    for (const kp of knownPaths) {
      if (fs.existsSync(kp)) candidates.push(kp);
    }
  }

  // 5. Test candidate executables for valid Python invocation
  for (const c of candidates) {
    try {
      const res = spawnSync(c, ['--version'], { encoding: 'utf-8', timeout: 3000 });
      if (res.status === 0) {
        supervisorLog('PYTHON_RESOLVED', { exe: c, version: (res.stdout || res.stderr).trim() });
        return { exe: c, argsPrefix: [] };
      }
    } catch (_) {}
  }

  // 6. Test 'python' in PATH
  try {
    const res = spawnSync('python', ['--version'], { encoding: 'utf-8', timeout: 3000 });
    if (res.status === 0) {
      supervisorLog('PYTHON_RESOLVED', { exe: 'python', version: (res.stdout || res.stderr).trim() });
      return { exe: 'python', argsPrefix: [] };
    }
  } catch (_) {}

  // 7. Test Windows Python launcher 'py -3'
  if (process.platform === 'win32') {
    try {
      const res = spawnSync('py', ['-3', '--version'], { encoding: 'utf-8', timeout: 3000 });
      if (res.status === 0) {
        supervisorLog('PYTHON_RESOLVED', { exe: 'py', argsPrefix: ['-3'], version: (res.stdout || res.stderr).trim() });
        return { exe: 'py', argsPrefix: ['-3'] };
      }
    } catch (_) {}
  }

  supervisorLog('PYTHON_FALLBACK_DEFAULT', { exe: 'python' });
  return { exe: 'python', argsPrefix: [] };
}

// Clean up stale or orphan python processes on port 8765 if not responding
async function handlePortConflict() {
  const isHealthy = await checkBackendHealth(600);
  if (isHealthy) {
    supervisorLog('PORT_ALREADY_HEALTHY', { port: PORT });
    return true; // Existing healthy ARIS backend, reuse cleanly
  }

  // On Windows, check if port is held by an unresponsive process
  if (process.platform === 'win32') {
    try {
      const netstat = spawnSync('netstat', ['-ano'], { encoding: 'utf-8' });
      const lines = (netstat.stdout || '').split('\n');
      for (const line of lines) {
        if (line.includes(`:${PORT}`) && line.includes('LISTENING')) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && pid !== '0' && pid !== process.pid.toString()) {
            supervisorLog('STALE_PORT_KILL', { port: PORT, pid });
            spawnSync('taskkill', ['/PID', pid, '/F', '/T']);
            await new Promise((r) => setTimeout(r, 600));
          }
        }
      }
    } catch (err) {
      supervisorLog('PORT_CLEANUP_ERROR', { error: err.message });
    }
  }
  return false;
}

// Terminate python process tree safely
function stopPythonBackend() {
  if (pythonProcess && pythonProcess.pid) {
    const pid = pythonProcess.pid;
    supervisorLog('TERMINATING_BACKEND', { pid });
    try {
      if (process.platform === 'win32') {
        spawnSync('taskkill', ['/PID', pid.toString(), '/T', '/F']);
      } else {
        pythonProcess.kill('SIGTERM');
      }
    } catch (err) {
      supervisorLog('TERMINATION_ERROR', { pid, error: err.message });
    }
    pythonProcess = null;
    activePid = null;
  }
}

// Start controlled Python backend child process
function startPythonBackend() {
  if (isShuttingDown) return;
  if (pythonProcess) return;

  const resolved = resolvePythonInterpreter();
  const args = [...resolved.argsPrefix, '-m', 'backend.api.app'];
  const canonicalDb = path.join(BACKEND_DIR, 'aris.db');

  const childEnv = {
    ...process.env,
    PYTHONUNBUFFERED: '1',
    PYTHONPATH: PROJECT_ROOT,
    ARIS_DB_PATH: canonicalDb
  };

  supervisorLog('SPAWN_REQUESTED', {
    exe: resolved.exe,
    args,
    cwd: PROJECT_ROOT,
    dbPath: canonicalDb
  });

  try {
    pythonProcess = spawn(resolved.exe, args, {
      cwd: PROJECT_ROOT,
      env: childEnv,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: false,
      windowsHide: true
    });

    activePid = pythonProcess.pid;
    supervisorLog('SPAWN_SUCCESS', { pid: activePid });

    // Pipe stdout and stderr to persistent log
    pythonProcess.stdout.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) supervisorLog('BACKEND_STDOUT', { output: msg });
    });

    pythonProcess.stderr.on('data', (data) => {
      const msg = data.toString().trim();
      if (msg) supervisorLog('BACKEND_STDERR', { output: msg });
    });

    pythonProcess.on('error', (err) => {
      supervisorLog('BACKEND_PROCESS_ERROR', { pid: activePid, error: err.message });
      handleBackendExit(-1, 'ERROR');
    });

    pythonProcess.on('exit', (code, signal) => {
      supervisorLog('BACKEND_PROCESS_EXIT', { pid: activePid, code, signal });
      handleBackendExit(code, signal);
    });

  } catch (err) {
    supervisorLog('SPAWN_EXCEPTION', { error: err.message });
    handleBackendExit(-1, 'SPAWN_EXCEPTION');
  }
}

// Automatic supervisor recovery upon unexpected process exit
async function handleBackendExit(code, signal) {
  pythonProcess = null;
  activePid = null;

  if (isShuttingDown) return;

  supervisorLog('UNEXPECTED_EXIT_DETECTED', { code, signal, restartAttempts, max: MAX_RESTART_ATTEMPTS });
  broadcastBackendStatus('RECOVERING', { attempt: restartAttempts + 1 });

  if (restartAttempts < MAX_RESTART_ATTEMPTS) {
    restartAttempts++;
    const backoffMs = Math.min(1000 * Math.pow(1.5, restartAttempts - 1), 5000);
    supervisorLog('SUPERVISOR_SCHEDULING_RESTART', { attempt: restartAttempts, backoffMs });

    setTimeout(async () => {
      if (isShuttingDown) return;
      await handlePortConflict();
      startPythonBackend();
      const healthy = await waitForBackend(10000);
      if (healthy) {
        supervisorLog('SUPERVISOR_RECOVERY_SUCCESS', { attempt: restartAttempts });
        restartAttempts = 0;
        broadcastBackendStatus('ONLINE');
      } else {
        supervisorLog('SUPERVISOR_RECOVERY_HEALTH_FAILED', { attempt: restartAttempts });
        handleBackendExit(-1, 'HEALTH_FAILED');
      }
    }, backoffMs);
  } else {
    supervisorLog('SUPERVISOR_RESTARTS_EXHAUSTED', { restartAttempts });
    broadcastBackendStatus('OFFLINE', {
      error: 'Backend crashed and exceeded automatic recovery attempts. Check backend_supervisor.log for diagnostics.'
    });
  }
}

// Create Electron Desktop Window
function createWindow() {
  const iconPath = path.join(__dirname, 'assets', 'icon.png');
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#080A10',
    title: 'ARIS',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false // allow local API calls to http://127.0.0.1:8765
    },
    show: false,
    autoHideMenuBar: true
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.maximize();
    mainWindow.show();
    // Emit initial status to loaded UI
    broadcastBackendStatus(backendState);
  });

  const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
  const devUrl = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173';

  // Probe dev server, fallback gracefully to dist/index.html
  let loaded = false;
  const loadFallback = () => {
    if (loaded) return;
    loaded = true;
    supervisorLog('LOAD_GUI_DIST', { indexPath });
    mainWindow.loadFile(indexPath);
  };

  const req = http.get(devUrl, (res) => {
    if (!loaded && res.statusCode && res.statusCode >= 200 && res.statusCode < 400) {
      loaded = true;
      supervisorLog('LOAD_GUI_DEV', { devUrl });
      mainWindow.loadURL(devUrl);
    } else {
      loadFallback();
    }
  });
  req.on('error', () => {
    loadFallback();
  });
  req.setTimeout(800, () => {
    req.destroy();
    loadFallback();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('get-backend-status', () => ({
  state: backendState,
  port: PORT,
  pid: activePid
}));

ipcMain.handle('restart-backend', async () => {
  supervisorLog('MANUAL_RESTART_REQUESTED');
  broadcastBackendStatus('RECOVERING', { manual: true });
  stopPythonBackend();
  await handlePortConflict();
  startPythonBackend();
  const ok = await waitForBackend(10000);
  if (ok) {
    restartAttempts = 0;
    broadcastBackendStatus('ONLINE');
    return { success: true };
  } else {
    broadcastBackendStatus('OFFLINE');
    return { success: false, error: 'Failed to restart backend' };
  }
});

// App Lifecycle
app.whenReady().then(async () => {
  broadcastBackendStatus('STARTING');

  // Check if healthy backend already running
  const alreadyRunning = await handlePortConflict();
  if (alreadyRunning) {
    supervisorLog('EXISTING_BACKEND_REUSED');
    backendState = 'ONLINE';
  } else {
    startPythonBackend();
    const healthy = await waitForBackend(20000);
    if (healthy) {
      backendState = 'ONLINE';
      supervisorLog('INITIAL_STARTUP_ONLINE');
    } else {
      backendState = 'RECOVERING';
      supervisorLog('INITIAL_STARTUP_UNRESPONSIVE');
    }
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('before-quit', () => {
  isShuttingDown = true;
  supervisorLog('APP_BEFORE_QUIT');
  stopPythonBackend();
});

app.on('will-quit', () => {
  isShuttingDown = true;
  supervisorLog('APP_WILL_QUIT');
  stopPythonBackend();
});

app.on('window-all-closed', () => {
  isShuttingDown = true;
  stopPythonBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
