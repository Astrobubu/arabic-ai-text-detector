const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs/promises');
const { spawn } = require('child_process');

const PORT = 8756;
let pyProc = null;
let mainWindow = null;

function resolveBackendCommand() {
  if (app.isPackaged) {
    const exeName = process.platform === 'win32' ? 'aidetect-server.exe' : 'aidetect-server';
    const backendDir = path.join(process.resourcesPath, 'backend');
    const modelCacheDir = path.join(backendDir, 'model_cache');
    return {
      cmd: path.join(backendDir, exeName),
      args: ['--port', String(PORT)],
      env: {
        ...process.env,
        AIDETECT_ARABIC_MODEL_DIR: path.join(modelCacheDir, 'arabic'),
        AIDETECT_ENGLISH_MODEL_DIR: path.join(modelCacheDir, 'english'),
      },
    };
  }
  const repoRoot = path.join(__dirname, '..');
  const venvPython = process.platform === 'win32'
    ? path.join(repoRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(repoRoot, '.venv', 'bin', 'python');
  const pythonExe = require('fs').existsSync(venvPython)
    ? venvPython
    : (process.platform === 'win32' ? 'python' : 'python3');
  return {
    cmd: pythonExe,
    args: ['-m', 'aidetect.server', '--port', String(PORT)],
    cwd: repoRoot,
    env: process.env,
  };
}

function startBackend() {
  const { cmd, args, cwd, env } = resolveBackendCommand();
  pyProc = spawn(cmd, args, { cwd: cwd || process.resourcesPath, env, stdio: 'ignore' });
  pyProc.on('error', (err) => {
    dialog.showErrorBox(
      'Local engine failed to start',
      `Could not start the analysis backend.\n\n${err.message}\n\n` +
      'If you are running from source, make sure Python and the project dependencies are installed ' +
      '(pip install -e ".[all]") and that "python" is on your PATH.'
    );
  });
}

function waitForHealth(retriesLeft = 120) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(`http://127.0.0.1:${PORT}/api/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
        res.resume();
      });
      req.on('error', retry);
    };
    const retry = () => {
      if (retriesLeft-- <= 0) {
        reject(new Error('The local analysis engine did not start in time.'));
        return;
      }
      setTimeout(attempt, 500);
    };
    attempt();
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1080,
    height: 800,
    minWidth: 760,
    minHeight: 560,
    backgroundColor: '#f4f5f7',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  mainWindow.setMenuBarVisibility(false);
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  try {
    await waitForHealth();
    mainWindow.webContents.send('backend-ready', { port: PORT });
    if (process.argv.includes('--self-test')) {
      console.log('SELF_TEST_OK backend_ready port=' + PORT);
      setTimeout(() => app.quit(), 1500);
    }
    const screenshotIdx = process.argv.indexOf('--screenshot');
    if (screenshotIdx !== -1) {
      await runScreenshotDemo(process.argv[screenshotIdx + 1] || 'demo.png');
    }
  } catch (err) {
    mainWindow.webContents.send('backend-error', { message: err.message });
    if (process.argv.includes('--self-test')) {
      console.log('SELF_TEST_FAIL ' + err.message);
      setTimeout(() => app.quit(), 500);
    }
  }
}

async function runScreenshotDemo(outPath) {
  const sample = [
    'من الجدير بالذكر أن هذا الموضوع يحظى باهتمام كبير في الآونة الأخيرة والعصر الحالي.',
    'علاوة على ذلك فإن التحليل الشامل يوضح أهمية النهج المتكامل في معالجة القضية المطروحة.',
    'وفي الختام يمكن القول إن هذا الأمر يمثل شهادة على أهمية التخطيط الدقيق والتنفيذ المنظم.',
    'ومن ناحية أخرى تجدر الإشارة إلى ضرورة مراعاة الجوانب المختلفة لهذا الموضوع الهام جدا جدا جدا.',
  ].join(' ').repeat(3);

  await mainWindow.webContents.executeJavaScript(`
    (function() {
      const ta = document.getElementById('text-input');
      ta.value = ${JSON.stringify(sample)};
      ta.dispatchEvent(new Event('input'));
    })();
  `);
  if (process.argv.includes('--lang-en')) {
    await mainWindow.webContents.executeJavaScript(`document.getElementById('lang-toggle').click();`);
  }
  if (process.argv.includes('--theme-light')) {
    await mainWindow.webContents.executeJavaScript(`document.getElementById('theme-toggle').click();`);
  }
  await mainWindow.webContents.executeJavaScript(`document.getElementById('analyze-btn').click();`);

  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    const done = await mainWindow.webContents.executeJavaScript(
      `!document.getElementById('results-panel').hidden`
    );
    if (done) break;
    await new Promise((r) => setTimeout(r, 500));
  }
  await new Promise((r) => setTimeout(r, 500));

  const image = await mainWindow.webContents.capturePage();
  await fs.writeFile(outPath, image.toPNG());
  console.log('SCREENSHOT_SAVED ' + outPath);
  setTimeout(() => app.quit(), 300);
}

ipcMain.handle('get-backend-port', () => PORT);

ipcMain.handle('export-pdf', async (_event, defaultName) => {
  const { canceled, filePath } = await dialog.showSaveDialog(mainWindow, {
    title: 'Save report as PDF',
    defaultPath: defaultName || 'ai-text-detector-report.pdf',
    filters: [{ name: 'PDF Document', extensions: ['pdf'] }],
  });
  if (canceled || !filePath) return { canceled: true };

  const data = await mainWindow.webContents.printToPDF({ printBackground: true, pageSize: 'A4' });
  await fs.writeFile(filePath, data);
  return { canceled: false, filePath };
});

app.whenReady().then(() => {
  startBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pyProc) pyProc.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (pyProc) pyProc.kill();
});
