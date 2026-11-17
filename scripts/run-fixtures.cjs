const assert = require('node:assert/strict');
const { readdir, writeFile } = require('node:fs/promises');
const { join, resolve } = require('node:path');
const { chromium } = require('playwright');

async function main() {
  const [, , directory, site = 'https://mp3tomidi.online/'] = process.argv;
  if (!directory) throw new Error('Usage: node scripts/run-fixtures.cjs <fixture-directory> [site-url]');

  const input = resolve(directory);
  const files = (await readdir(input)).filter(name => /\.(?:mp3|wav)$/.test(name)).sort();
  assert.ok(files.length, 'The fixture directory must contain MP3 or WAV inputs');
  const browser = await chromium.launch({ channel: 'chrome' });
  const records = [];
  try {
    const page = await browser.newPage({ acceptDownloads: true, offline: site.startsWith('file:') });
    for (const file of files) {
      await page.goto(site);
      await page.locator('#file').setInputFiles(join(input, file));
      await page.locator('#convert').click();
      await page.waitForFunction(() =>
        document.querySelector('#download').hasAttribute('href') || !document.querySelector('#error').hidden
      );
      if (await page.locator('#error').isVisible()) {
        const message = (await page.locator('#error').innerText()).trim();
        assert.match(message, /^No sustained notes found\./, file);
        assert.equal(await page.locator('#download').getAttribute('href'), null);
        records.push({ file, notes: 0, export: null, message });
        continue;
      }
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        page.locator('#download').click(),
      ]);
      const output = file + '.mid';
      await download.saveAs(join(input, output));
      const notes = Number(await page.locator('#note-count').innerText());
      assert.ok(Number.isInteger(notes) && notes > 0, file);
      records.push({ file, notes, export: output });
    }
    const log = { chrome: browser.version(), records };
    await writeFile(join(input, 'browser.json'), JSON.stringify(log, null, 2) + '\n');
    console.log(JSON.stringify(log, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
