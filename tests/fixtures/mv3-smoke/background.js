const bootId = crypto.randomUUID();

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create('zaid-wake-test', {delayInMinutes: 1});
});

chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === 'zaid-wake-test') {
    await chrome.storage.local.set({lastAlarm: Date.now(), alarmBootId: bootId});
  }
});

async function runChecks() {
  const results = [];
  async function check(name, fn) {
    try {
      results.push({name, ok: true, detail: await fn()});
    } catch (error) {
      results.push({name, ok: false, detail: String(error)});
    }
  }
  await check('runtime / service worker', async () => {
    if (chrome.runtime.getManifest().manifest_version !== 3) throw new Error('Not MV3');
    return `Worker ${bootId}`;
  });
  await check('storage.local', async () => {
    const value = crypto.randomUUID();
    await chrome.storage.local.set({roundtrip: value});
    if ((await chrome.storage.local.get('roundtrip')).roundtrip !== value) {
      throw new Error('Storage roundtrip failed');
    }
    return 'Lectura y escritura correctas';
  });
  await check('tabs / scripting', async () => {
    const tabs = await chrome.tabs.query({url: 'https://example.com/*'});
    const tab = tabs.find(candidate => Number.isInteger(candidate.id));
    if (!tab) throw new Error('Abre https://example.com y vuelve a ejecutar la prueba');
    const injected = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: () => {
        document.documentElement.dataset.zaidScripting = 'ok';
        return {origin: location.origin, marker: document.documentElement.dataset.zaidScripting};
      },
    });
    if (injected[0]?.result?.marker !== 'ok') throw new Error('Injection failed');
    return JSON.stringify(injected[0].result);
  });
  await check('userScripts', async () => {
    if (!chrome.userScripts) throw new Error('Activa Permitir scripts de usuario en Detalles de esta extensión');
    const id = 'zaid-userscript-smoke';
    if ((await chrome.userScripts.getScripts({ids: [id]})).length) {
      await chrome.userScripts.unregister({ids: [id]});
    }
    await chrome.userScripts.register([{
      id,
      matches: ['https://example.com/*'],
      js: [{code: "document.documentElement.dataset.zaidUserScript = 'ok';"}],
      runAt: 'document_idle',
    }]);
    const scripts = await chrome.userScripts.getScripts({ids: [id]});
    if (scripts.length !== 1) throw new Error('Registration failed');
    return 'Registrado. Recarga example.com y comprueba la ejecución.';
  });
  await check('persistencia / alarma', async () => {
    const saved = await chrome.storage.local.get(['previousBoot', 'lastAlarm', 'alarmBootId']);
    await chrome.storage.local.set({previousBoot: bootId});
    await chrome.alarms.create('zaid-wake-test', {delayInMinutes: 1});
    if (!saved.lastAlarm) throw new Error('Alarma programada; espera un minuto y repite la prueba');
    return JSON.stringify({currentBoot: bootId, ...saved});
  });
  return results;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id || message?.type !== 'run-checks') return;
  runChecks().then(sendResponse, error => sendResponse([{name: 'worker', ok: false, detail: String(error)}]));
  return true;
});
