document.querySelector('#open').addEventListener('click', () => {
  chrome.tabs.create({url: 'https://example.com/'});
});
document.querySelector('#run').addEventListener('click', async event => {
  event.target.disabled = true;
  const output = document.querySelector('#results');
  output.textContent = 'Ejecutando…';
  try {
    const results = await chrome.runtime.sendMessage({type: 'run-checks'});
    output.textContent = results.map(row => `${row.ok ? 'OK' : 'ERROR'}: ${row.name}\n${row.detail}`).join('\n\n');
  } catch (error) {
    output.textContent = String(error);
  } finally {
    event.target.disabled = false;
  }
});
