// Production bundle, local catalog, intercepted API; no listeners/providers.
import assert from 'node:assert/strict';
import {readFile, mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const dist=fileURLToPath(new URL('../dist/',import.meta.url));
const shots=fileURLToPath(new URL('../../../docs/design/p410-qa/',import.meta.url));
await mkdir(shots,{recursive:true});
const browser=await chromium.launch();
let checks=0;
const evidence=[];
try {
 for(const width of [375,768,1440]) {
  const context=await browser.newContext({viewport:{width,height:1000},hasTouch:width===375,isMobile:width===375});
  const page=await context.newPage(), errors=[], submissions=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.hostname==='127.0.0.1') {
    const send=(json,status=200)=>route.fulfill({json,status,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'content-type,authorization','Access-Control-Allow-Methods':'GET,POST,OPTIONS'}});
    if(route.request().method()==='OPTIONS') return send({});
    if(url.pathname.endsWith('/capabilities')) return send({providers:[{provider_id:'fake',enabled:true,permitted_to_aggregate:true},{provider_id:'fake2',enabled:true,permitted_to_aggregate:true}],supported_currencies:['IDR'],max_route_date_combinations:4,synthetic_mode:true});
    if(url.pathname.endsWith('/searches')) {submissions.push(route.request().postDataJSON());return send({detail:'Synthetic submission captured'},422);}
    throw new Error('Unexpected API path '+url.pathname);
   }
   assert.equal(url.hostname,'localhost');
   const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
   assert.ok(!path.includes('..'));
   const types={js:'text/javascript',css:'text/css',html:'text/html',json:'application/json',svg:'image/svg+xml'};
   try{return route.fulfill({body:await readFile(dist+path),contentType:types[path.split('.').at(-1)]??'application/octet-stream'});}
   catch{return route.fulfill({status:404,body:''});}
  });
  await page.goto('http://localhost:5173/');
  const origin=page.getByRole('combobox',{name:'Origin airports',exact:true});
  const destination=page.getByRole('combobox',{name:'Destination airports',exact:true});
  await origin.fill('cgk'); await origin.press('Enter');
  assert.equal(await page.getByRole('button',{name:'Remove CGK',exact:true}).count(),1);checks++;
  await destination.fill('Japan'); await destination.press('Enter');
  assert.equal(await page.getByRole('button',{name:'Remove HND',exact:true}).count(),0);checks++;
  await destination.fill('HND'); await destination.press('Enter');
  assert.equal(await destination.getAttribute('aria-expanded'),'true');checks++;
  await destination.fill('NRT'); await destination.press('Enter');
  assert.equal(submissions.length,0);checks++;
  await destination.press('Escape');assert.equal(await destination.getAttribute('aria-expanded'),'false');checks++;
  await page.getByRole('list',{name:'Destination airports selected airports'}).getByText(/NRT/).waitFor();
  await page.screenshot({path:`${shots}/specific_${width}.png`,fullPage:true});
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
  await page.getByText('Synthetic submission captured',{exact:true}).waitFor();
  assert.deepEqual(submissions[0].destinations,['HND','NRT']);checks++;
  assert.deepEqual(submissions[0].origins,['CGK']);checks++;
  const modes=page.getByRole('group',{name:'Destination airports coverage mode'});
  await modes.getByRole('button',{name:'Major Airports',exact:true}).click();
  await page.getByRole('button',{name:'Keep Specific Airports',exact:true}).click();
  assert.equal(await page.getByRole('button',{name:'Remove NRT',exact:true}).count(),1);checks++;
  await modes.getByRole('button',{name:'Major Airports',exact:true}).click();
  await page.getByRole('button',{name:'Clear airports and choose Major',exact:true}).click();
  await destination.fill('TYO');
  if(width===375) await page.getByRole('option').filter({hasText:'Tokyo'}).tap(); else await destination.press('Enter');
  await page.getByText('Tokyo · Japan · 2 airports included',{exact:true}).waitFor();
  await page.getByText('Major airports only — not all airports in this location',{exact:true}).waitFor();
  assert.equal(await page.getByRole('list',{name:'Destination airports selected airports'}).getByRole('listitem').count(),2);checks++;
  await page.screenshot({path:`${shots}/major_${width}.png`,fullPage:true});
  const secondResponse=page.waitForResponse(r=>r.url().endsWith('/searches') && r.request().method()==='POST');
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
  await secondResponse;
  assert.equal(submissions.length,2);checks++;
  assert.equal(submissions[1].destination_selection.location_id,'metro:JP:TYO');checks++;
  assert.deepEqual(submissions[1].destinations,['HND','NRT']);checks++;
  await destination.fill('United States');await destination.press('Enter');
  await page.getByText(/No curated major-airport mapping for United States/).waitFor();
  assert.equal(await page.getByRole('list',{name:'Destination airports selected airports'}).count(),0);checks++;
  await destination.fill('Japan');await destination.press('Enter');
  assert.equal(await page.getByRole('button',{name:'Find cheapest flights',exact:true}).isDisabled(),true);checks++;
  assert.equal(await page.getByRole('list',{name:'Destination airports selected airports'}).getByRole('listitem').count(),8);checks++;
  await page.getByText(/8 route-date combinations/).waitFor();
  await page.screenshot({path:`${shots}/over_cap_${width}.png`,fullPage:true});
  await modes.getByRole('button',{name:'Specific Airports',exact:true}).click();
  assert.equal(await page.getByRole('button',{name:'Remove NRT',exact:true}).count(),1);checks++;
  assert.equal(await page.getByRole('list',{name:'Destination airports selected airports'}).getByRole('listitem').count(),8);checks++;
  for(const code of ['CTS','FUK','ITM','KIX','NGO','OKA']) await page.getByRole('button',{name:`Remove ${code}`,exact:true}).click();
  await page.getByLabel('Earliest departure',{exact:true}).fill('2027-01-01');
  await page.getByLabel('Latest departure',{exact:true}).fill('2027-01-02');
  await page.getByText(/4 route-date combinations/).waitFor();
  assert.equal(await page.getByRole('button',{name:'Find cheapest flights',exact:true}).isDisabled(),false);checks++;
  await page.getByText(/Estimated upper bound: 8 provider work items/).waitFor();
  await page.getByLabel('Latest departure',{exact:true}).fill('2027-01-03');
  assert.equal(await page.getByRole('button',{name:'Find cheapest flights',exact:true}).isDisabled(),true);checks++;
  await page.getByText(/6 route-date combinations/).waitFor();
  await page.getByRole('button',{name:'Remove NRT',exact:true}).click();
  await origin.fill('HND');await origin.press('Enter');
  await page.getByText(/3 route-date combinations/).waitFor();
  await page.getByRole('button',{name:'Remove CGK',exact:true}).click();
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
  await page.getByText('No valid routes. Choose different origin and destination airports.',{exact:true}).waitFor();
  assert.equal(submissions.length,2);checks++;
  await origin.fill('Soekarno');await origin.press('Space');
  assert.equal(await origin.inputValue(),'Soekarno ');checks++;
  await origin.fill('CGK');await origin.press('ArrowDown');await origin.press('ArrowUp');await origin.press('Space');
  assert.equal(await page.getByRole('button',{name:'Remove CGK',exact:true}).count(),1);checks++;
  await destination.fill('HND');await destination.press('ArrowDown');
  const activeId=await destination.getAttribute('aria-activedescendant');
  assert.ok(activeId);assert.equal(await page.locator(`[id="${activeId}"]`).getAttribute('role'),'option');checks++;
  await destination.press('Escape');
  assert.deepEqual(errors,[]);checks++;
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);checks++;
  evidence.push({width,scenario:'Specific, Major, unmapped, mode-switch, over-cap, dates, overlap, keyboard, mobile',codes:submissions[0].destinations,autoSubmissions:0,overflow:false});
  await context.close(); console.log('PASS P4.10 integration '+width);
 }
} finally {await browser.close();}
await writeFile(shots+'/evidence.json',JSON.stringify({checks,evidence},null,2)+'\n');
console.log(`${checks} P4.10 browser assertions passed`);
