// P4.12 status visuals against the built UI; synthetic API only, no providers.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const dist=fileURLToPath(new URL('../dist/',import.meta.url));
const now='2027-01-10T12:00:00Z';
const status=(provider_id,succeeded,pending,running,failed=0)=>({provider_id,succeeded,pending,running,retry_wait:0,failed,cancelled:0,skipped_unsupported:0,disabled_reason:null});
const job={job_id:'p412',query:{origins:['MEL'],destinations:['DPS'],departure_date_from:'2027-01-12',departure_date_through:'2027-01-14',display_currency:'IDR',max_stops:null,checked_bags_required:false,include_basic_economy:true,include_hidden_city:false},
 status:'running',phase:'searching',cancel_requested:false,created_at:now,updated_at:now,total_route_date_combinations:3,covered_route_date_combinations:2,
 total_provider_work_items:12,succeeded_provider_work_items:5,succeeded_empty:0,failed_provider_work_items:3,skipped_unsupported:0,cancelled_provider_work_items:0,
 inventory_completeness:'unknown',exact_reprice_attempted:0,exact_reprice_succeeded:0,data_expires_at:null,provider_ids:['fli','skiplagged','octotrip','swoop'],
 provider_status:[status('fli',3,0,0),status('skiplagged',1,1,1),status('octotrip',1,0,2),status('swoop',0,0,0,3)],coverage:[],warnings:[]};
const pool={global_capacity:16,low_priority_headroom:2,running:11,providers:[
 {provider_id:'fli',priority:0,running:4,wait_ms:0,cooling_down:false},
 {provider_id:'skiplagged',priority:0,running:3,wait_ms:1400,cooling_down:false},
 {provider_id:'octotrip',priority:1,running:4,wait_ms:52000,cooling_down:true}]};
const browser=await chromium.launch();
let checks=0;
try {
 for(const [width,poolOk] of [[375,true],[1440,true],[1440,false]]) {
  const context=await browser.newContext({viewport:{width,height:1000}});
  const page=await context.newPage();
  const errors=[];let poolCalls=0;
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',async route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.hostname==='127.0.0.1') {
    const send=(json,code=200)=>route.fulfill({json,status:code,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,authorization'}});
    if(req.method()==='OPTIONS') return send({});
    if(url.pathname.endsWith('/capabilities')) return send({providers:job.provider_ids.map(provider_id=>({provider_id,enabled:true,permitted_to_aggregate:true})),supported_currencies:['IDR'],max_route_date_combinations:120,max_active_jobs:2,max_hourly_jobs:20,synthetic_mode:true,inventory_completeness:'unknown'});
    if(url.pathname.endsWith('/worker/pool')) {poolCalls++;return poolOk?send(pool):send({detail:'down'},503);}
    if(url.pathname.endsWith('/results')) return send({job_id:'p412',sort:'best_checked',status:'running',as_of:now,next_cursor:null,itineraries:[],expired_observations:[],warnings:[]});
    if(url.pathname.endsWith('/searches/p412')) return send(job);
    throw new Error('Unexpected API path '+url.pathname);
   }
   const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
   assert.ok(!path.includes('..'));
   try{return route.fulfill({body:await readFile(dist+path),contentType:({html:'text/html',css:'text/css',js:'text/javascript',svg:'image/svg+xml'})[path.split('.').at(-1)]??'application/octet-stream'});}
   catch{return route.fulfill({status:404,body:''});}
  });
  await page.goto('http://localhost:5173/?job=p412');
  const summary=page.getByText('Source coverage and caveats',{exact:true});
  await summary.waitFor();
  assert.equal(poolCalls,0,'pool is not polled while the dropdown is closed');checks++;
  await summary.click();
  for(const label of ['Fli (Google Flights): 3 done','Skiplagged: 1 done, 1 running, 1 queued','OctoTrip: 1 done, 2 running','swoop (Google Flights): 3 failed'])
   {await page.getByRole('img',{name:label,exact:true}).waitFor();checks++;}
  if(poolOk) {
   await page.getByText('Worker pool 11 / 16 busy',{exact:true}).waitFor();checks++;
   await page.getByRole('img',{name:'11 of 16 worker slots busy: Fli (Google Flights) 4, Skiplagged 3, OctoTrip 4',exact:true}).waitFor();checks++;
   assert.equal(await page.locator('.sv-cell.sv-reserved').count(),2);checks++;
   await page.getByText('cooldown 52s').waitFor();await page.getByText('pacing, next start 1.4s').waitFor();checks++;
  } else {await page.getByText('Pool status unavailable.',{exact:true}).waitFor();checks++;}
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),`no horizontal overflow at ${width}`);checks++;
  await summary.click();
  const calls=poolCalls;await page.waitForTimeout(2500);
  assert.equal(poolCalls,calls,'polling stops when the dropdown closes');checks++;
  assert.deepEqual(errors,[]);checks++;
  await context.close();
 }
} finally {await browser.close();}
console.log(`P4.12 browser: ${checks} assertions passed`);
