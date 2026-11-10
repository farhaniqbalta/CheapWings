// P4.6 acceptance checks against the ACTUAL React dist bundle, not preview HTML.
// Requires `npm run build` and installed Playwright Chromium. All API responses are synthetic.
import assert from 'node:assert/strict';
import { readFile, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const now = '2027-01-10T12:00:00Z';
const job = { job_id:'p46-synthetic', query:{origins:['MEL'],destinations:['DPS','CGK'],departure_date_from:'2027-01-12',departure_date_through:'2027-01-15',display_currency:'AUD',max_stops:null,checked_bags_required:false,include_basic_economy:true},
  status:'completed',phase:'done',cancel_requested:false,created_at:now,updated_at:now,
  total_route_date_combinations:8, covered_route_date_combinations:6,total_provider_work_items:16,
  succeeded_provider_work_items:11,succeeded_empty:2,failed_provider_work_items:2,
  skipped_unsupported:2,cancelled_provider_work_items:1,inventory_completeness:'unknown',
  exact_reprice_attempted:0,exact_reprice_succeeded:0,data_expires_at:null,
  provider_status:[{provider_id:'fake',succeeded:11,failed:2,cancelled:1,skipped_unsupported:2,disabled_reason:null}],
  coverage:[],warnings:['SYNTHETIC SOURCE PARTIAL COVERAGE'] };
const offer = (id,name,amount) => ({ quote_id:id, provider_id:'fake', seller:name,
  fare_family:null,cabin:'economy',basic_economy:null,amount_original:amount,currency_original:'AUD',
  comparable_amount:amount,comparable_currency:'AUD',comparison_status:'extra_cost_unknown',
  checked_bag:'unknown',hidden_city:'unknown',self_transfer:'unknown',price_status:'indicative',
  is_estimate:true,retrieved_at:now,repriced_at:null,link:null,link_scope:'unavailable',warnings:['SYNTHETIC source quotation only'] });
const trip = (id,to,price) => ({ itinerary_id:id,identity_confidence:'exact_segments',
  origin:'MEL',destination:to,departure_local:now,arrival_local:now,duration_minutes:495,stops:0,
  ranked_quote_id:id,warnings:['SYNTHETIC ITINERARY'],segments:[{ordinal:1,marketing_carrier:'FAKE',operating_carrier:'FAKE',flight_number:'TEST-1',origin:'MEL',destination:to,depart_at:now,arrive_at:now}],
  offers:[offer(id,`SYNTHETIC SELLER ${id}`,price)] });
const all = [trip('one','DPS','418.00'),trip('two','CGK','445.00')];
const shots = process.env.P46_SCREENSHOT_DIR ?? '/tmp/cheapwings-p46-qa';
await mkdir(shots,{recursive:true});
const browser = await chromium.launch();

// Additional integration coverage for the latest cache/evidence contract and selection lifecycle.
async function fixturePage(width, state) {
  const context=await browser.newContext({viewport:{width,height:1000},hasTouch:width===375});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  state.submissions=[];
  await context.route('**/*',async route=>{
    const req=route.request(),url=new URL(req.url());
    if(url.hostname==='127.0.0.1') {
      const send=(json,status=200)=>route.fulfill({json,status,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,authorization','Access-Control-Allow-Methods':'GET,POST,OPTIONS'}});
      if(req.method()==='OPTIONS')return send({});
      if(url.pathname.endsWith('/capabilities'))return send({synthetic_mode:true,search_cache_enabled:true,supported_currencies:['IDR','USD','AUD','JPY'],max_route_date_combinations:120});
      if(req.method()==='POST'&&url.pathname.endsWith('/searches')) {
        state.submissions.push(req.postDataJSON());state.jobId='p46-fresh';
        return send({job_id:state.jobId,status:'queued',job_status_url:'/api/v1/searches/'+state.jobId},202);
      }
      const id=url.pathname.split('/')[4];
      if(url.pathname.endsWith('/results'))return send({job_id:id,sort:url.searchParams.get('sort'),status:state.status??'completed',as_of:now,next_cursor:null,itineraries:state.entries??all,warnings:['SYNTHETIC test observations only.']});
      return send({...job,...state.job,job_id:id,status:state.status??'completed',provider_ids:['fake'],updated_at:`2027-01-10T12:00:${String(state.revision??0).padStart(2,'0')}Z`});
    }
    if(url.hostname!=='localhost')return route.fulfill({contentType:'text/html',body:'<h1>SYNTHETIC external destination</h1>'});
    const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
    if(path.includes('..'))return route.abort();
    try{return route.fulfill({body:await readFile(dist+path),contentType:({html:'text/html',css:'text/css',js:'text/javascript'})[path.split('.').at(-1)]??'application/octet-stream'});}
    catch{return route.fulfill({status:404,body:''});}
  });
  return {context,page,errors};
}

async function noOverflow(page,label) {
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,label);
}

const richEntries=Array.from({length:5},(_,index)=>({
  ...trip('rich-'+index,['DPS','CGK','SUB','DPS','CGK'][index],String(418+index*27)+'.00'),
  departure_local:'2027-01-12T07:00:00+11:00',arrival_local:'2027-01-12T11:30:00+08:00',
  carrier_names:['SYNTHETIC Airline '+(index+1)],
  segments:[{ordinal:0,marketing_carrier:'XY',operating_carrier:'XZ',marketing_carrier_name:'SYNTHETIC Airline',operating_carrier_name:'SYNTHETIC Operator',flight_number:String(100+index),origin:'MEL',destination:['DPS','CGK','SUB','DPS','CGK'][index],depart_at:'2027-01-12T07:00:00+11:00',arrive_at:'2027-01-12T11:30:00+08:00'}],
}));
richEntries[0].offers=[
  {...offer('cheaper','SYNTHETIC lower-confidence seller','399.00'),result_origin:'shared_inflight'},
  {...offer('rich-0','SYNTHETIC FX SELLER','209.00'),comparable_amount:'418.00',currency_original:'USD',fx_rate:'2',fx_as_of:now,attribution:'SYNTHETIC source attribution',point_of_sale_country:'AU',result_origin:'cache',reused_at:now,link:'https://example.org/synthetic-search',link_scope:'generic_search'},
  {...offer('long','SYNTHETIC '+('LongSellerName'.repeat(12)),'9999999999999999.99'),price_status:'repriced_exact',is_estimate:true,warnings:['SYNTHETIC '+('Long uncertainty detail without verified seller evidence. '.repeat(8))]},
];
richEntries[1]={...richEntries[1],identity_confidence:'insufficient_identity',segments:[],departure_local:'2027-01-12T07:00:00',arrival_local:'2027-01-12T11:30:00'};
richEntries[2]={...richEntries[2],airport_transfers:[{after_segment:0,from_airport:'NRT',to_airport:'HND'}]};

try {
  for (const width of [375,768,1440]) {
    const context = await browser.newContext({viewport:{width,height:900}});
    const page = await context.newPage();
    const errors=[]; let providerCalls=0;
    page.on('pageerror',e=>errors.push(e.message));
    await page.route('**/*',async route => {
      const req=route.request(),url=new URL(req.url());
      if (url.hostname==='127.0.0.1') {
        providerCalls++;
        const send=(json,status=200)=>route.fulfill({json,status,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,authorization','Access-Control-Allow-Methods':'GET,POST,OPTIONS'}});
        if(req.method()==='OPTIONS')return send({});
        if(url.pathname.endsWith('/capabilities'))return send({synthetic_mode:true,supported_currencies:['AUD'],max_route_date_combinations:120,inventory_completeness:'unknown',providers:[]});
        if(url.pathname.endsWith('/results'))return send({job_id:'p46-synthetic',sort:url.searchParams.get('sort'),status:'completed',as_of:now,next_cursor:null,itineraries:all,warnings:[]});
        return send(job);
      }
      const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
      if(path.includes('..'))return route.abort();
      try{return route.fulfill({body:await readFile(dist+path),contentType:({html:'text/html',css:'text/css',js:'text/javascript',svg:'image/svg+xml'})[path.split('.').at(-1)] ?? 'application/octet-stream'});}
      catch{return route.fulfill({status:404,body:''});}
    });
    await page.goto('http://localhost:5173/?job=p46-synthetic');
    await page.locator('.p46-ledger-row').first().waitFor();
    await page.getByText('SYNTHETIC SELLER one',{exact:false}).first().waitFor();
    assert.equal(await page.locator('.p46-ledger-row').count(),2);
    assert.match(await page.locator('.p46-ledger-row').first().getAttribute('aria-pressed'),/^true$/);
    assert.match(await page.locator('.p46-job-strip').innerText(),/ROUTE\/DATE\s+6\/8/);
    assert.match(await page.locator('.p46-job-strip').innerText(),/PROVIDER WORK\s+11\/16/);
    const before=providerCalls;
    await page.locator('.p46-ledger-row').nth(1).click();
    assert.equal(await page.locator('.p46-ledger-row').nth(1).getAttribute('aria-pressed'),'true');
    await page.locator('.p46-dossier').getByText('SYNTHETIC SELLER two',{exact:false}).waitFor();
    assert.equal(providerCalls,before,'Selecting an itinerary must not request new network data');
    assert.equal(await page.locator('.p46-dossier .itinerary-best-price').innerText(),'AUD 445.00');
    await page.getByRole('button',{name:'View 1 flight leg'}).click();
    assert.equal(await page.locator('.p46-leg-list').isVisible(),true);
    await page.getByText('Price evidence and restrictions',{exact:true}).click();
    assert.equal(await page.locator('.p46-evidence-body').isVisible(),true);
    assert.match(await page.locator('.p46-seller-riskline').innerText(),/Unknown/);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${width}px horizontal page overflow`);
    await page.getByRole('button',{name:'New search',exact:false}).click();
    await page.getByRole('button',{name:'Find cheapest flights',exact:true}).waitFor();
    assert.deepEqual(errors,[]);
    await context.close();
    console.log(`PASS p46 master-detail, disclosure, source evidence and search ${width}px`);
  }

  for(const width of [375,768,1440]) {
    {
      const state={};const {context,page,errors}=await fixturePage(width,state);
      await page.goto('http://localhost:5173/');
      const submit=page.getByRole('button',{name:'Find cheapest flights',exact:true});
      const origin=page.getByLabel('Origin airports',{exact:true}),destination=page.getByLabel('Destination airports',{exact:true});
      await origin.fill('BADCODE');await origin.press('Enter');
      await page.getByText(/not a 3-letter airport code/).waitFor();
      await origin.fill('mel');await origin.press('Enter');await origin.fill('MEL');await origin.press('Enter');
      assert.equal(await page.getByRole('button',{name:'Remove MEL',exact:true}).count(),1);
      await destination.fill('MEL');await destination.press('Enter');await submit.click();
      await page.getByText('Origin and destination airports cannot overlap.',{exact:true}).waitFor();
      await page.locator('.p46-route-fields .field').nth(1).getByRole('button',{name:'Remove MEL'}).click();
      await destination.fill('DPS');await destination.press('Enter');await destination.fill('CGK');await destination.press('Enter');
      await page.getByLabel('Earliest departure',{exact:true}).fill('2027-01-12');
      await page.getByLabel('Latest departure',{exact:true}).fill('2027-01-11');await submit.click();
      assert.equal(await page.getByLabel('Latest departure',{exact:true}).evaluate(input=>input.validity.rangeUnderflow),true);
      assert.equal(state.submissions.length,0);
      await page.getByLabel('Latest departure',{exact:true}).fill('2027-12-30');assert.equal(await submit.isDisabled(),true);
      await page.getByLabel('Latest departure',{exact:true}).fill('2027-01-15');
      await page.getByLabel('Checked bag required',{exact:true}).check();await page.getByLabel('Include basic economy',{exact:true}).uncheck();
      await page.getByText('More search settings',{exact:true}).click();
      await page.getByLabel('Maximum stops',{exact:true}).selectOption('1');await page.getByLabel('Display currency',{exact:true}).selectOption('AUD');
      await page.getByLabel('Include hidden-city fares',{exact:true}).check();await page.getByText(/Hidden-city fares carry airline-enforcement risk/).waitFor();
      await page.getByText(/8 route-date combinations/).waitFor();
      await noOverflow(page,`search ${width}`);
      await submit.click();await page.waitForURL('**/?job=p46-fresh');
      await page.getByRole('button',{name:'New search',exact:false}).click();
      await page.getByRole('button',{name:'Find cheapest flights',exact:true}).waitFor();
      await page.getByLabel('Origin airports',{exact:true}).fill('MEL');await page.getByLabel('Origin airports',{exact:true}).press('Enter');
      await page.getByLabel('Destination airports',{exact:true}).fill('DPS');await page.getByLabel('Destination airports',{exact:true}).press('Enter');
      await page.getByLabel('Destination airports',{exact:true}).fill('CGK');await page.getByLabel('Destination airports',{exact:true}).press('Enter');
      await page.getByLabel('Earliest departure',{exact:true}).fill('2027-01-12');await page.getByLabel('Latest departure',{exact:true}).fill('2027-01-15');
      await page.screenshot({path:`${shots}/search_${width}.png`,fullPage:true});
      assert.deepEqual(state.submissions[0],{origins:['MEL'],destinations:['DPS','CGK'],departure_date_from:'2027-01-12',departure_date_through:'2027-01-15',max_stops:1,checked_bags_required:true,include_basic_economy:false,include_hidden_city:true,display_currency:'AUD'});
      assert.deepEqual(errors,[]);await context.close();console.log(`PASS p46 validated search payload ${width}px`);
    }
    {
      const state={entries:richEntries,job:{coverage:[{work_type:'detailed',status:'succeeded_results',provider_id:'fake',unpriced_candidate_count:0,result_origin:'cache'}]}};
      const {context,page,errors}=await fixturePage(width,state);
      await page.goto('http://localhost:5173/?job=p46-synthetic');await page.locator('.p46-dossier').waitFor();
      assert.equal(await page.locator('.itinerary-best-price').innerText(),'AUD 418.00');
      await page.getByText(/Cached observation/).first().waitFor();await page.getByText('Shared source observation',{exact:true}).waitFor();
      await page.getByText('Estimate — exact price unconfirmed',{exact:true}).waitFor();
      await page.getByText('Price evidence and restrictions',{exact:true}).nth(1).click();
      await page.getByText(/Original: USD 209.00/).waitFor();await page.getByText(/FX rate 2/).waitFor();
      const link=page.getByRole('link',{name:/Open source search from SYNTHETIC FX SELLER/});
      assert.equal(await link.getAttribute('rel'),'noopener noreferrer nofollow');
      const popupPromise=page.waitForEvent('popup');await link.click();const popup=await popupPromise;
      await popup.getByText('SYNTHETIC external destination',{exact:true}).waitFor();await popup.close();
      await noOverflow(page,`evidence ${width}`);
      if(width===1440){
        const geometry=await page.evaluate(()=>({master:document.querySelector('.p46-master').getBoundingClientRect().width,detail:document.querySelector('.p46-detail').getBoundingClientRect().width,row:document.querySelector('.p46-ledger-row').getBoundingClientRect().height}));
        assert.ok(geometry.master/(geometry.master+geometry.detail)>.55&&geometry.master/(geometry.master+geometry.detail)<.59);
        console.log('P46 row height',geometry.row);
        assert.ok(geometry.row>=100&&geometry.row<=115,'Desktop rows stay within the reference density');
        console.log('P46 desktop geometry',JSON.stringify(geometry));
      }
      await page.screenshot({path:`${shots}/results_${width}.png`,fullPage:true});
      await page.evaluate(()=>document.documentElement.style.fontSize='20px');await noOverflow(page,`enlarged root text ${width}`);
      await page.evaluate(()=>document.body.style.zoom='1.25');await noOverflow(page,`125 percent zoom ${width}`);
      await page.evaluate(()=>{document.documentElement.style.fontSize='16px';document.body.style.zoom='1';});
      await page.locator('.p46-ledger-row').nth(1).click();await page.getByText('Flight-leg detail unavailable. Times above are source summary values.',{exact:true}).waitFor();
      await page.getByText(/timezone unknown/).first().waitFor();
      await page.locator('.p46-ledger-row').nth(2).click();await page.getByText(/NRT → HND/).waitFor();
      assert.deepEqual(errors,[]);await context.close();console.log(`PASS p46 evidence, links, unknowns and zoom ${width}px`);
    }
    {
      const state={status:'running',entries:all,revision:0};const {context,page,errors}=await fixturePage(width,state);
      await page.goto('http://localhost:5173/?job=p46-synthetic');await page.locator('.p46-ledger-row').first().waitFor();
      const selected=()=>page.locator('.p46-ledger-row[aria-pressed="true"]');
      await page.locator('.p46-ledger-row').nth(1).focus();await page.keyboard.press('Enter');
      assert.match(await selected().innerText(),/CGK/);
      assert.notEqual(await selected().evaluate(element=>getComputedStyle(element).outlineStyle),'none');
      await page.getByRole('button',{name:'View 1 flight leg',exact:true}).click();
      const nextResults=()=>page.waitForResponse(response=>response.url().includes('/results'));
      let reply=nextResults();state.entries=[all[1],all[0]];state.revision++;await reply;
      assert.match(await selected().innerText(),/CGK/);assert.equal(await page.locator('.segments').isVisible(),true);
      reply=nextResults();state.entries=[all[0]];state.revision++;await reply;await page.locator('.p46-dossier').getByText('SYNTHETIC SELLER one',{exact:true}).waitFor();
      reply=nextResults();state.entries=[all[1],all[0]];state.revision++;await reply;
      assert.match(await selected().innerText(),/DPS/,'Disappearing selection falls back persistently');
      await page.getByRole('button',{name:'Lowest advertised',exact:true}).click();
      await page.locator('.p46-dossier').getByText('SYNTHETIC SELLER two',{exact:true}).waitFor();
      state.entries=all;
      await page.getByRole('button',{name:'Run fresh search',exact:true}).click();await page.waitForURL('**/?job=p46-fresh');
      await page.locator('.p46-dossier').getByText('SYNTHETIC SELLER one',{exact:true}).waitFor();
      assert.deepEqual(state.submissions[0].provider_ids,['fake']);assert.equal(state.submissions[0].cache_mode,'refresh');
      assert.equal(state.submissions.length,1,'Selection and polling must never POST');
      const partialReply=page.waitForResponse(response=>response.url().includes('/results'));
      state.status='partial';state.revision++;await partialReply;
      await page.getByText('Partially complete',{exact:true}).waitFor();
      await noOverflow(page,`selection ${width}`);
      await page.screenshot({path:`${shots}/partial_${width}.png`,fullPage:true});
      assert.deepEqual(errors,[]);await context.close();console.log(`PASS p46 selection polling, keyboard, fallback and scope reset ${width}px`);
    }
  }
} finally {await browser.close();}
