// P7.5 Discover UI against the built app; synthetic API only, no providers. All prices fictitious.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const dist=fileURLToPath(new URL('../dist/',import.meta.url));
const now='2027-02-20T00:00:00Z';
const lead=(destination,comparable_amount,checked_amount=null)=>({origin:'CGK',destination,date:'2027-03-01',comparable_amount,checked_amount,checked_itinerary_id:checked_amount?'sin1':null});
const djob=(job_id,status,extra={})=>({job_id,provider_ids:['fli','skiplagged'],status,phase:status==='running'?'searching':'done',cancel_requested:false,
 created_at:now,updated_at:now,query:{origins:['CGK'],departure_date_from:'2027-03-01',departure_date_through:'2027-03-02',display_currency:'IDR',budget:null,max_stops:null},
 discovery:{calls_planned:2,calls_done:2,calls_failed:0,unpriced:3,discovered_destinations:2,counts:{selected:2},outcome:'planned',stopped_providers:[],shortlist:status==='running'?[lead('DPS','640000'),lead('SIN','800000')]:[lead('DPS','640000'),lead('SIN','800000','750000')]},
 total_checks:4,succeeded_checks:status==='running'?1:4,failed_checks:0,checked_route_dates:status==='running'?0:2,provider_status:[],
 warnings:['Lowest fares found among 2 discovered destinations; 1 checked. Not every destination in the world was searched.'],...extra});
const offer=amount=>({quote_id:'q',provider_id:'fli',seller:'SYNTHETIC',fare_family:null,cabin:'economy',basic_economy:null,amount_original:amount,currency_original:'IDR',
 comparable_amount:amount,comparable_currency:'IDR',comparison_status:'extra_cost_unknown',checked_bag:'unknown',hidden_city:'no',self_transfer:'no',price_status:'indicative',
 is_estimate:true,retrieved_at:now,repriced_at:null,link:null,link_scope:'unavailable',warnings:[]});
const sin={itinerary_id:'sin1',identity_confidence:'insufficient_identity',origin:'CGK',destination:'SIN',departure_local:'2027-03-01T07:00:00+07:00',
 arrival_local:'2027-03-01T10:00:00+08:00',duration_minutes:120,stops:0,segments:[],carrier_names:['Synthetic Air'],offers:[offer('750000')],ranked_quote_id:'q'};
const results=(job_id,itineraries)=>({job_id,sort:'lowest_advertised',status:'completed',as_of:now,next_cursor:null,itineraries,expired_observations:[],warnings:[]});
const unavailable=djob('dfail','failed',{discovery:{calls_planned:2,calls_done:2,calls_failed:2,unpriced:0,discovered_destinations:0,counts:null,outcome:'unavailable',stopped_providers:['skiplagged'],shortlist:[]},
 total_checks:0,succeeded_checks:0,checked_route_dates:0,warnings:['Lowest fares found among 0 discovered destinations; 0 checked. Not every destination in the world was searched.']});
const browser=await chromium.launch();
let checks=0;
try {
 for(const width of [375,1440]) {
  const context=await browser.newContext({viewport:{width,height:1000}});
  const page=await context.newPage();
  const errors=[];let polls=0;let posted=null;
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',async route=>{
   const req=route.request(),url=new URL(req.url());
   if(url.hostname==='127.0.0.1') {
    const send=(json,code=200)=>route.fulfill({json,status:code,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,authorization'}});
    if(req.method()==='OPTIONS') return send({});
    if(url.pathname.endsWith('/capabilities')) return send({providers:[
      {provider_id:'fli',enabled:true,permitted_to_aggregate:true,detailed_search:true,destination_discovery:false},
      {provider_id:'skiplagged',enabled:true,permitted_to_aggregate:true,detailed_search:true,destination_discovery:true}],
      supported_currencies:['IDR','USD'],max_route_date_combinations:120,max_active_jobs:2,max_hourly_jobs:20,synthetic_mode:true,inventory_completeness:'unknown'});
    if(url.pathname==='/api/v1/discover'&&req.method()==='POST'){posted=JSON.parse(req.postData());return send({job_id:'d1',status:'queued',created_at:now,discovery_calls:2,enabled_detailed_providers:['fli','skiplagged'],job_status_url:'/api/v1/discover/d1'},202);}
    if(url.pathname==='/api/v1/discover/d1') {polls++;return send(polls<2?djob('d1','running'):djob('d1','completed'));}
    if(url.pathname==='/api/v1/discover/d1/results') return send(results('d1',polls<2?[]:[sin]));
    if(url.pathname==='/api/v1/discover/dfail') return send(unavailable);
    if(url.pathname==='/api/v1/discover/dfail/results') return send(results('dfail',[]));
    throw new Error('Unexpected API path '+url.pathname);
   }
   const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
   assert.ok(!path.includes('..'));
   try{return route.fulfill({body:await readFile(dist+path),contentType:({html:'text/html',css:'text/css',js:'text/javascript',svg:'image/svg+xml',json:'application/json'})[path.split('.').at(-1)]??'application/octet-stream'});}
   catch{return route.fulfill({status:404,body:''});}
  });
  await page.goto('http://localhost:5173/');
  await page.getByRole('button',{name:'Discover',exact:true}).click();
  const form=page.getByRole('form',{name:'Discover destinations'});
  await form.waitFor();checks++;
  const origin=page.getByLabel('Origin airports',{exact:true});
  await origin.fill('CGK');await origin.press('Enter');
  await page.getByLabel('Earliest departure').fill('2027-03-01');
  await page.getByLabel('Latest departure').fill('2027-04-01');
  await page.getByText('32 discovery calls',{exact:false}).waitFor();checks++;
  const submit=page.getByRole('button',{name:/Discover destinations/});
  assert.equal(await submit.isDisabled(),true,'over 31 calls disables submit');checks++;
  await page.getByLabel('Latest departure').fill('2027-03-02');
  await page.getByText('2 discovery calls',{exact:false}).waitFor();checks++;
  await submit.click();
  await page.waitForURL(/discover=d1/);checks++;
  assert.deepEqual([posted.origins,posted.departure_date_from,posted.departure_date_through],[['CGK'],'2027-03-01','2027-03-02']);checks++;
  await page.getByText('Discovery price (provisional)').first().waitFor();checks++;
  await page.getByText('Lowest fares found among 2 discovered destinations; 1 checked.',{exact:false}).waitFor({timeout:15000});checks++;
  const firstRow=page.locator('.discover-row').first();
  await firstRow.getByText('SIN').waitFor();await firstRow.getByText('Checked fare').waitFor();checks++;
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),`no horizontal overflow at ${width}`);checks++;
  // Review fix: the pressed toggle does nothing, and switching modes and back keeps the Discover run.
  await page.getByRole('button',{name:'Discover',exact:true}).click();
  await page.waitForURL(/discover=d1/);checks++;
  await page.getByRole('button',{name:'Search',exact:true}).click();
  await page.getByRole('form',{name:'Flight search'}).waitFor();checks++;
  await page.getByRole('button',{name:'Discover',exact:true}).click();
  await page.getByText('Lowest fares found among 2 discovered destinations; 1 checked.',{exact:false}).waitFor();checks++;
  await page.goto('http://localhost:5173/?discover=dfail');
  await page.getByText('could not be reached',{exact:false}).waitFor();checks++;
  assert.equal(await page.locator('.discover-row').count(),0,'no rows when the source was unavailable');checks++;
  assert.deepEqual(errors,[]);checks++;
  await context.close();
 }
} finally {await browser.close();}
console.log(`P7.5 browser: ${checks} assertions passed`);
