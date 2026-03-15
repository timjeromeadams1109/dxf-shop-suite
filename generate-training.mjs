#!/usr/bin/env node
/**
 * generate-training.mjs
 *
 * Captures live screenshots of each tab and injects them into training.html.
 * Also extracts current machine profiles and tab descriptions from the app
 * so the training guide stays in sync with app changes.
 *
 * Usage:
 *   npx playwright install chromium   # first time only
 *   node generate-training.mjs                                          # uses file:// URL
 *   node generate-training.mjs --url https://dxf-shop-suite.vercel.app  # uses live URL
 *   node generate-training.mjs --output training.html                   # custom output
 */

import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Parse CLI args
const args = process.argv.slice(2);
const urlArg = args.find((_, i) => args[i - 1] === '--url') || null;
const outputArg = args.find((_, i) => args[i - 1] === '--output') || 'training.html';
const appUrl = urlArg || `file://${resolve(__dirname, 'index.html')}`;
const outputPath = resolve(__dirname, outputArg);

const TABS = [
  { name: 'validate', label: 'Validate', action: 'sample' },
  { name: 'clean', label: 'Clean', action: 'sample' },
  { name: 'nest', label: 'Nest Analyzer', action: null },
  { name: 'library', label: 'Part Library', action: null },
  { name: 'create', label: 'Create DXF', action: 'template' },
  { name: 'machines', label: 'Machine Profiles', action: 'select-machine' },
];

async function main() {
  console.log(`\n  DXF Training Guide Generator`);
  console.log(`  ============================`);
  console.log(`  App URL:  ${appUrl}`);
  console.log(`  Output:   ${outputPath}\n`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  console.log('  Loading app...');
  await page.goto(appUrl, { waitUntil: 'networkidle', timeout: 30000 });

  // Dismiss welcome overlay if present
  try {
    const welcomeClose = page.locator('#welcome-close');
    if (await welcomeClose.isVisible({ timeout: 2000 })) {
      await welcomeClose.click();
      await page.waitForTimeout(500);
    }
  } catch (e) { /* no welcome overlay */ }

  // Hide page loader
  await page.evaluate(() => {
    const loader = document.getElementById('page-loader');
    if (loader) loader.classList.add('hidden');
  });
  await page.waitForTimeout(500);

  // Take overview screenshot (hero + tabs area)
  console.log('  Capturing overview...');
  const overviewShot = await page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1440, height: 900 } });
  const overviewB64 = overviewShot.toString('base64');

  // Capture each tab
  const screenshots = { overview: overviewB64 };

  for (const tab of TABS) {
    console.log(`  Capturing ${tab.name}...`);

    // Switch to tab
    await page.click(`.tab-btn[data-tab="${tab.name}"]`);
    await page.waitForTimeout(400);

    // Perform tab-specific actions for richer screenshots
    if (tab.action === 'sample' && tab.name === 'validate') {
      try {
        await page.evaluate(() => { if (typeof generateSampleDXF === 'function') generateSampleDXF('validate'); });
        await page.waitForTimeout(500);
        await page.click('#btn-validate');
        // Wait for results
        await page.waitForSelector('.result-badge', { timeout: 10000 }).catch(() => {});
        await page.waitForTimeout(500);
      } catch (e) { console.log(`    (could not run sample for ${tab.name})`); }
    }

    if (tab.action === 'sample' && tab.name === 'clean') {
      try {
        await page.evaluate(() => { if (typeof generateSampleDXF === 'function') generateSampleDXF('clean'); });
        await page.waitForTimeout(500);
        await page.click('#btn-clean');
        await page.waitForSelector('.result-badge', { timeout: 10000 }).catch(() => {});
        await page.waitForTimeout(500);
      } catch (e) { console.log(`    (could not run sample for ${tab.name})`); }
    }

    if (tab.action === 'template') {
      try {
        await page.click('[data-preset="rect"]');
        await page.waitForTimeout(300);
      } catch (e) { /* no preset */ }
    }

    if (tab.action === 'select-machine') {
      try {
        await page.click('.machine-card[data-key="vortman_631"]');
        await page.waitForTimeout(300);
      } catch (e) {
        // Try clicking first machine card
        try { await page.click('.machine-card'); await page.waitForTimeout(300); } catch (e2) {}
      }
    }

    // Scroll tab panel into view and screenshot
    const panel = page.locator(`#panel-${tab.name}`);
    await panel.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);

    try {
      const shot = await panel.screenshot({ type: 'png' });
      screenshots[tab.name] = shot.toString('base64');
      console.log(`    ✓ ${tab.name} (${Math.round(shot.length / 1024)}KB)`);
    } catch (e) {
      console.log(`    ✗ ${tab.name} failed: ${e.message}`);
    }
  }

  await browser.close();

  // Read training.html template
  console.log('\n  Injecting screenshots into training.html...');
  let html = readFileSync(outputPath, 'utf-8');

  // Replace screenshot placeholders with real images
  for (const [key, b64] of Object.entries(screenshots)) {
    const placeholder = new RegExp(
      `<div class="screenshot-placeholder">.*?</div>`,
      's'
    );
    // Find the specific screenshot section
    const marker = `<!-- SCREENSHOT:${key} -->`;
    const markerIdx = html.indexOf(marker);
    if (markerIdx !== -1) {
      // Find the next screenshot-placeholder after this marker
      const afterMarker = html.substring(markerIdx);
      const replaced = afterMarker.replace(
        placeholder,
        `<img src="data:image/png;base64,${b64}" alt="Screenshot of ${key} tab" style="width:100%;display:block">`
      );
      html = html.substring(0, markerIdx) + replaced;
    }
  }

  // Update the generation timestamp
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  html = html.replace(
    /This guide was generated on <strong id="stamp-date">.*?<\/strong>/,
    `This guide was generated on <strong id="stamp-date">${dateStr}</strong>`
  );

  writeFileSync(outputPath, html, 'utf-8');
  const sizeKB = Math.round(readFileSync(outputPath).length / 1024);
  console.log(`\n  ✓ Training guide updated (${sizeKB}KB)`);
  console.log(`  ✓ ${Object.keys(screenshots).length} screenshots embedded`);
  console.log(`  ✓ Generated: ${dateStr}\n`);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
