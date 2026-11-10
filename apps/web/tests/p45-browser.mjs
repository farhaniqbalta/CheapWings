// Integrated React acceptance using intercepted synthetic APIs only.
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const shots = process.env.P45_SCREENSHOT_DIR ?? '/tmp/cheapwings-p45-qa';
await mkdir(shots, { recursive: true });
const timestamp = '2027-01-10T12:00:00Z';
const query = { origins: ['MEL'], destinations: ['DPS'], departure_date_from: '2027-01-10',
 departure_date_through: '2027-01-12', display_currency: 'IDR', checked_bags_required: false };
const baseJob = { job_id: 'p45-test', query, status: 'completed', phase: 'done', cancel_requested: false,
 created_at: timestamp, updated_at: timestamp, total_route_date_combinations: 3,
 covered_route_date_combinations: 2, total_provider_work_items: 6, succeeded_provider_work_items: 4,
 succeeded_empty: 1, failed_provider_work_items: 1, skipped_unsupported: 0,
 cancelled_provider_work_items: 1, inventory_completeness: 'unknown',
 exact_reprice_attempted: 0, exact_reprice_succeeded: 0,
 provider_status: [{provider_id:'fixture',succeeded:4,failed:1,cancelled:1,skipped_unsupported:0,disabled_reason:null}],
 coverage: [{work_type:'detailed',provider_id:'fixture',unpriced_candidate_count:2,error_code:'schema_changed'}],
 warnings: ['SYNTHETIC: some source work failed.', 'Some source candidates had no price; see unpriced_candidate_count in coverage.'] };
const commonOffer = {provider_id:'fixture',seller:'SYNTHETIC Seller',fare_family:'standard',cabin:'economy',
 basic_economy:false,amount_original:'4250000',currency_original:'IDR',comparable_amount:'4250000',
 comparable_currency:'IDR',price_status:'recent_search',comparison_status:'eligible_total_known',
 checked_bag:'yes',hidden_city:'no',self_transfer:'no',is_estimate:false,retrieved_at:timestamp,
 repriced_at:null,link:null,link_scope:'unavailable',warnings:[],attribution:'SYNTHETIC source'};
const itinerary = {itinerary_id:'synthetic-itin',identity_confidence:'exact_segments',origin:'MEL',
 destination:'DPS',departure_local:'2027-01-10T07:00:00+11:00',arrival_local:'2027-01-10T10:00:00+08:00',
 duration_minutes:360,stops:0,ranked_quote_id:'ranked',warnings:[],
 segments:[{ordinal:0,marketing_carrier:'FX',operating_carrier:'FX',flight_number:'100',origin:'MEL',
 destination:'DPS',depart_at:'2027-01-10T07:00:00+11:00',arrive_at:'2027-01-10T10:00:00+08:00'}],
 carrier_names:['SYNTHETIC Airline'],
 offers:[{...commonOffer,quote_id:'ranked'}, {...commonOffer,quote_id:'cheaper',seller:'SYNTHETIC Alternate',
 amount_original:'3990000',comparable_amount:'3990000',is_estimate:true,price_status:'indicative',
 hidden_city:'unknown',checked_bag:'unknown',comparison_status:'extra_cost_unknown',basic_economy:null}]};
const browser = await chromium.launch();
let scenarios = 0;
try {
 for (const width of [375,768,1440]) {
  for (const scene of ['search','partial','results','cancelled-empty','empty-success','queued','verifying','polling','airport-change','failed','expired','rate-limit','offline']) {
   const context=await browser.newContext({viewport:{width,height:1000}});
   const page=await context.newPage(); const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   let polls=0;
   await page.route('**/*',async route=> {
    const req=route.request(),url=new URL(req.url());
    if(url.hostname==='127.0.0.1') {
     const send=(json,status=200)=>route.fulfill({json,status,headers:{'Access-Control-Allow-Origin':'*',
      'Access-Control-Allow-Headers':'content-type,authorization','Access-Control-Allow-Methods':'GET,POST,OPTIONS'}});
     if(req.method()==='OPTIONS')return send({});
     if(url.pathname.endsWith('/capabilities'))return send({synthetic_mode:true,supported_currencies:['IDR'],max_route_date_combinations:120});
     if(scene==='offline')return route.abort('failed');
     if(scene==='rate-limit')return send({detail:'SYNTHETIC quota exceeded'},429);
     if(url.pathname.endsWith('/results')) {
      if(scene==='expired')return send({detail:'SYNTHETIC fare evidence expired'},410);
      const airportChanged={...itinerary,stops:1,airport_transfers:[{after_segment:0,from_airport:'NRT',to_airport:'HND'}],
        segments:[{...itinerary.segments[0],destination:'NRT'}, {...itinerary.segments[0],ordinal:1,origin:'HND',flight_number:'200'}],
        offers:itinerary.offers.map(offer=>({...offer,comparison_status:'extra_cost_unknown'}))};
      const items=['failed','queued','empty-success'].includes(scene)||
        (scene==='airport-change'&&url.searchParams.get('sort')==='best_checked')||(scene==='cancelled-empty'&&url.searchParams.get('sort')==='best_checked')?[]:[scene==='airport-change'?airportChanged:itinerary];
      return send({job_id:'p45-test',sort:url.searchParams.get('sort'),status:'completed',as_of:timestamp,next_cursor:null,itineraries:items,warnings:['SYNTHETIC quotes only.']});
     }
     const status=scene==='partial'?'partial':scene==='cancelled-empty'?'cancelled':scene==='failed'?'failed'
       :scene==='queued'?'queued':['verifying','polling'].includes(scene)?'running':'completed';
     const partial=scene==='partial'||scene==='cancelled-empty';
     const noCoverage=['failed','queued'].includes(scene);
     const succeeded=noCoverage?0:partial?4:6,failed=scene==='failed'?6:partial?1:0;
     polls++;
     return send({...baseJob,status,phase:scene==='verifying'?'verifying':status==='running'||status==='queued'?'searching':'done',
       updated_at:scene==='polling'?`2027-01-10T12:00:${String(polls).padStart(2,'0')}Z`:timestamp,
       covered_route_date_combinations:noCoverage?0:partial?2:3,
       succeeded_provider_work_items:succeeded,failed_provider_work_items:failed,
       succeeded_empty:scene==='empty-success'?6:noCoverage?0:1,cancelled_provider_work_items:partial?1:0,
       provider_status:[{provider_id:'fixture',succeeded,failed,cancelled:partial?1:0,skipped_unsupported:0,disabled_reason:null}],
       coverage:[{work_type:'detailed',provider_id:'fixture',unpriced_candidate_count:noCoverage?0:2,error_code:failed?'schema_changed':null}],
       warnings:partial?baseJob.warnings:[]});
    }
    const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
    if(path.includes('..'))return route.abort();
    try{return route.fulfill({body:await readFile(dist+path),contentType:({js:'text/javascript',css:'text/css',html:'text/html'})[path.split('.').at(-1)]??'application/octet-stream'});}
    catch{return route.fulfill({status:404,body:''});}
   });
   await page.goto('http://localhost:5173/'+(scene==='search'?'':'?job=p45-test'));
   if(scene==='search') {
    await page.getByText(/SYNTHETIC · Demonstration/).waitFor();
    if(width===375) {
     await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
     await page.getByText('Add at least one origin and one destination airport.',{exact:true}).waitFor();
    }
   } else if(scene==='airport-change') {
    await page.getByRole('button',{name:'Lowest advertised',exact:true}).click();
    await page.getByText('Airport change required:',{exact:true}).waitFor();
    await page.getByText(/NRT → HND/).waitFor();
    assert.match(await page.locator('.carrier-summary').innerText(),/SYNTHETIC Airline/);
    assert.match(await page.locator('.flight-numbers').innerText(),/FX100 · FX200/);
   } else if(scene==='offline')await page.getByText('Could not update this search',{exact:true}).waitFor();
   else if(scene==='queued')await page.getByText(/Source searches are still in progress/).waitFor();
   else if(scene==='empty-success')await page.getByText(/No matching fares returned/).waitFor();
   else if(scene==='expired')await page.getByText('These fare results have expired',{exact:true}).waitFor();
   else if(scene==='rate-limit')await page.getByText('Search request limit reached',{exact:true}).waitFor();
   else if(scene==='failed') {
    await page.getByText('The search did not return usable source coverage.',{exact:true}).waitFor();
    assert.equal(await page.getByText(/No matching fares returned/).count(),0);
   } else if(scene==='cancelled-empty') {
    await page.getByRole('button',{name:'View lower-confidence advertised offers',exact:true}).waitFor();
    await page.getByRole('button',{name:'View lower-confidence advertised offers',exact:true}).click();
    await page.locator('.itinerary-card').waitFor();
   } else {
    await page.locator('.itinerary-card').waitFor();
    assert.equal(await page.locator('.itinerary-best-price').innerText(),'IDR 4,250,000');
    assert.equal(await page.locator('.carrier-summary').innerText(),'SYNTHETIC Airline');
    assert.equal(await page.locator('.flight-numbers').innerText(),'FX100');
    await page.getByRole('button',{name:'View 1 flight leg',exact:true}).click();
    assert.equal(await page.locator('.segments').isVisible(),true);
    if(scene==='polling') {
      await page.waitForResponse(r=>r.url().includes('/results?'));
      await page.waitForTimeout(250);
      assert.equal(await page.locator('.segments').isVisible(),true,'Expanded flight details must survive polling');
    }
    if(scene==='verifying')await page.getByText('Checking selected prices',{exact:true}).waitFor();
    await page.getByRole('button',{name:'Hide flight legs',exact:true}).click();
    if(width===375&&scene==='results') {
     await page.getByText('Price evidence and restrictions',{exact:true}).first().click();
     assert.equal(await page.locator('.offer-provenance').first().isVisible(),true);
     await page.getByText('Price evidence and restrictions',{exact:true}).first().click();
    }
   }
   await page.getByText('Private server access',{exact:true}).focus();
   await page.keyboard.press('Enter');
   const token=page.getByLabel('Owner access token');await token.waitFor();
   await token.focus();
   const focus=await token.evaluate(element=>getComputedStyle(element).outlineStyle);
   assert.notEqual(focus,'none');
   await page.getByText('Private server access',{exact:true}).click();
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${scene} overflow at ${width}`);
   await page.evaluate(()=>document.documentElement.style.fontSize='20px');
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${scene} enlarged text overflow at ${width}`);
   await page.evaluate(()=>document.documentElement.style.fontSize='');
   if(['search','partial','results'].includes(scene))await page.screenshot({path:`${shots}/${scene}_${width}.png`,fullPage:true});
   assert.deepEqual(errors,[]);
   await context.close();scenarios++;
   console.log(`PASS ${scene} ${width}`);
  }
 }
 console.log(`PASS ${scenarios} state/viewport combinations; integrated screenshots in ${shots}`);
} finally {await browser.close();}
