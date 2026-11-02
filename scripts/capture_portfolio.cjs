const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

async function main() {
  const output = path.resolve(__dirname, '../docs/portfolio');
  await fs.mkdir(output, { recursive: true });
  const videoDirectory = await fs.mkdtemp(path.join(os.tmpdir(), 'framesignal-demo-'));
  const browser = await chromium.launch({ channel: 'msedge', headless: true, slowMo: 250 });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    recordVideo: { dir: videoDirectory, size: { width: 1440, height: 1000 } },
  });
  const page = await context.newPage();
  const video = page.video();
  const evidence = { screenshots: [], scenarios: {}, review_status: 'self-review only' };
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));

  async function screenshot(name) {
    await page.screenshot({ path: path.join(output, name), fullPage: true, animations: 'disabled' });
    evidence.screenshots.push(name);
  }

  try {
    await page.goto('http://127.0.0.1:8080/');
    await page.locator('.target-verdict').waitFor({ timeout: 120000 });
    await page.getByRole('button', { name: 'Run experiment', exact: true }).waitFor();
    for (const scenario of ['Helpful', 'Unrelated', 'Misleading']) {
      if (scenario !== 'Helpful') {
        const responsePromise = page.waitForResponse(response =>
          response.url().includes(`/api/analysis?scenario=${scenario.toLowerCase()}&`) && response.ok(),
          { timeout: 120000 });
        await page.getByRole('button', { name: scenario, exact: true }).click();
        await responsePromise;
      }
      await page.getByRole('button', { name: 'Run experiment', exact: true }).waitFor();
      assert.equal(await page.getByRole('spinbutton', { name: 'Households', exact: true }).inputValue(), '2000');
      assert.equal(await page.getByRole('spinbutton', { name: 'Seed', exact: true }).inputValue(), '20261031');
      evidence.scenarios[scenario.toLowerCase()] = await page.locator('.target-verdict').innerText();
      await screenshot(`framesignal-${scenario.toLowerCase()}.png`);
      await page.getByText('Same households. Different signals.', { exact: true }).scrollIntoViewIfNeeded();
      await page.locator('.page-heading').scrollIntoViewIfNeeded();
    }
    await page.getByRole('button', { name: 'Proxy validation', exact: true }).click();
    await page.getByText('Loading frozen validation suite', { exact: false }).waitFor({ state: 'hidden' });
    await page.locator('.recharts-surface').first().waitFor({ timeout: 120000 });
    await screenshot('framesignal-heldout-validation.png');

    await page.goto('http://127.0.0.1:8082/');
    await page.getByText('Educational use only', { exact: true }).waitFor({ timeout: 60000 });
    await page.getByRole('combobox', { name: 'Scientific status', exact: true }).selectOption({ label: 'Rejected surrogate' });
    await screenshot('metricsteward-rejected-catalog.png');
    const approvalBlock = page.getByText('Real-world approval blocked', { exact: true });
    await approvalBlock.scrollIntoViewIfNeeded();
    assert.equal(await approvalBlock.isVisible(), true);
    assert.equal(await page.getByText('Self-review only; no external peer review or real-world validation.', { exact: true }).count(), 1);
    await screenshot('metricsteward-promotion-blocked.png');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('heading', { name: 'MetricSteward', exact: true }).scrollIntoViewIfNeeded();
    const dimensions = await page.evaluate(() => ({
      content: document.documentElement.scrollWidth,
      viewport: document.documentElement.clientWidth,
    }));
    assert.ok(dimensions.content <= dimensions.viewport, 'MetricSteward mobile page overflows');
    evidence.mobile = dimensions;
    await screenshot('metricsteward-mobile.png');
    assert.deepEqual(pageErrors, [], 'Browser emitted runtime errors');
    evidence.browser_runtime_errors = pageErrors;
  } finally {
    await context.close();
    if (video) await video.saveAs(path.join(output, 'framesignal-metricsteward-demo.webm'));
    await browser.close();
    await fs.rm(videoDirectory, { recursive: true, force: true });
  }
  await fs.writeFile(path.join(output, 'capture-evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence, null, 2));
}

main().catch(error => { console.error(error); process.exitCode = 1; });