// Deterministic browser regression checks against the production bundle.
// Playwright intercepts both static assets and API requests: no localhost listener
// or upstream provider calls. Run npm run build first.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const timestamp = '2027-01-10T12:00:00Z';
const job = { query: { origins: ['MEL'], destinations: ['DPS'], departure_date_from: '2027-01-10', departure_date_through: '2027-01-10', display_currency: 'IDR', checked_bags_required: false }, job_id: 'test-job', status: 'completed', phase: 'done', cancel_requested: false,
  created_at: timestamp, updated_at: timestamp, total_route_date_combinations: 1,
  covered_route_date_combinations: 1, total_provider_work_items: 1,
  succeeded_provider_work_items: 1, succeeded_empty: 0, failed_provider_work_items: 0,
  skipped_unsupported: 0, cancelled_provider_work_items: 0, inventory_completeness: 'unknown',
  exact_reprice_attempted: 0, exact_reprice_succeeded: 0, provider_status: [], coverage: [], warnings: [] };
const capabilities = { synthetic_mode: true, supported_currencies: ['IDR'], max_route_date_combinations: 120 };
const itinerary = id => ({ itinerary_id: id, identity_confidence: 'insufficient_identity',
  origin: 'MEL', destination: 'DPS', departure_local: timestamp, arrival_local: timestamp,
  duration_minutes: 300, stops: 0, segments: [], ranked_quote_id: id, warnings: ['SYNTHETIC TEST'],
  offers: [{ quote_id: id, provider_id: 'fake', seller: `SYNTHETIC TEST SELLER ${id}`,
    amount_original: '1000', currency_original: 'IDR', comparable_amount: '1000', comparable_currency: 'IDR',
    price_status: 'indicative', comparison_status: 'extra_cost_unknown', checked_bag: 'unknown',
    hidden_city: 'unknown', self_transfer: 'unknown', is_estimate: true,
    retrieved_at: timestamp, repriced_at: null, link: null, link_scope: 'unavailable', warnings: [] }] });
const response = (items, cursor = null) => ({ job_id: 'test-job', sort: 'lowest_advertised',
  status: 'completed', as_of: timestamp, next_cursor: cursor, itineraries: items, warnings: [] });

const browser = await chromium.launch();
try {
  for (const scenario of ['empty-pagination-reload', 'runtime-auth', 'expiry', 'cancel']) {
    const context = await browser.newContext({ viewport: { width: 375, height: 850 } });
    const page = await context.newPage();
    const errors = [];
    let cancelled = false;
    page.on('pageerror', error => errors.push(error.message));
    await page.route('**/*', async route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.hostname === '127.0.0.1') {
        const send = (json, status = 200) => route.fulfill({ json, status,
          headers: { 'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'content-type,authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS' } });
        if (request.method() === 'OPTIONS') return send({});
        if (scenario === 'runtime-auth' && request.headers().authorization !== 'Bearer session-test-token') {
          return send({ detail: 'Owner bearer token required' }, 401);
        }
        if (url.pathname.endsWith('/capabilities')) return send(capabilities);
        if (url.pathname.endsWith('/cancel')) { cancelled = true; return send({ ...job, status: 'cancelled' }); }
        if (url.pathname.endsWith('/results')) {
          if (scenario === 'expiry') return send({ detail: 'Live fare data expired; start a new search' }, 410);
          if (scenario === 'empty-pagination-reload' && url.searchParams.get('sort') === 'best_checked') {
            return send({ ...response([]), sort: 'best_checked' });
          }
          if (url.searchParams.get('cursor')) return send(response([itinerary('second')]));
          return send({ ...response([itinerary('first')], scenario === 'empty-pagination-reload' ? 'page2' : null),
            sort: url.searchParams.get('sort') });
        }
        return send({ ...job, ...(scenario === 'cancel' ? { status: cancelled ? 'cancelled' : 'running',
          phase: cancelled ? 'done' : 'searching', updated_at: cancelled ? '2027-01-10T12:00:01Z' : timestamp } : {}) });
      }
      const path = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
      if (path.includes('..')) return route.abort();
      const types = { js: 'text/javascript', css: 'text/css', html: 'text/html', svg: 'image/svg+xml' };
      try { return route.fulfill({ body: await readFile(dist + path),
        contentType: types[path.split('.').at(-1)] ?? 'application/octet-stream' }); }
      catch { return route.fulfill({ status: 404, body: '' }); }
    });
    await page.goto('http://localhost:5173/?job=test-job');
    if (scenario === 'empty-pagination-reload') {
      await page.getByText(/No matching fares returned/).waitFor();
      await page.getByRole('button', { name: 'Lowest advertised', exact: true }).click();
      await page.getByText('SYNTHETIC TEST SELLER first', { exact: false }).waitFor();
      await page.getByRole('button', { name: 'Load more results' }).click();
      await page.getByText('SYNTHETIC TEST SELLER second', { exact: false }).waitFor();
      await page.reload();
      await page.getByText(/No matching fares returned/).waitFor();
      assert.equal(new URL(page.url()).searchParams.get('job'), 'test-job');
    } else if (scenario === 'runtime-auth') {
      await page.getByText('Owner bearer token required', { exact: true }).first().waitFor();
      await page.getByText('Private server access', { exact: true }).click();
      await page.getByLabel('Owner access token').fill('session-test-token');
      await page.getByRole('button', { name: 'Apply access token' }).click();
      await page.getByText('SYNTHETIC TEST SELLER first', { exact: false }).waitFor();
      assert.equal(await page.evaluate(() => localStorage.length + sessionStorage.length), 0);
    } else if (scenario === 'expiry') {
      await page.getByText('Live fare data expired; start a new search', { exact: true }).waitFor();
      assert.equal(await page.getByText('SYNTHETIC TEST SELLER first', { exact: false }).count(), 0);
    } else {
      await page.getByRole('button', { name: 'Cancel search', exact: true }).click();
      await page.getByText('Search cancelled.', { exact: true }).waitFor();
      await page.getByText('SYNTHETIC TEST SELLER first', { exact: false }).waitFor();
    }
    assert.deepEqual(errors, []);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await context.close();
    console.log(`PASS ${scenario}`);
  }
} finally { await browser.close(); }
