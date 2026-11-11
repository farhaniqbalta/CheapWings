// Fourth-source integration against the actual built UI; synthetic API only.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const dist=fileURLToPath(new URL('../dist/',import.meta.url));
const browser=await chromium.launch();
let checks=0;
try {
 for(const width of [375,1440]) {
  const context=await browser.newContext({viewport:{width,height:1000}});
  const page=await context.newPage();
  const submissions=[];
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await context.route('**/*',async route=>{
   const url=new URL(route.request().url());
   if(url.hostname==='127.0.0.1') {
    const send=(json,status=200)=>route.fulfill({json,status,headers:{'Access-Control-Allow-Origin':'*'}});
    if(url.pathname.endsWith('/capabilities')) return send({providers:['skiplagged','swoop','octotrip','fli'].map(provider_id=>({provider_id,enabled:true,permitted_to_aggregate:true})),supported_currencies:['IDR'],max_route_date_combinations:120,synthetic_mode:false});
    if(url.pathname.endsWith('/searches')) {submissions.push(route.request().postDataJSON());return send({detail:'P4.11 synthetic submission'},422);}
    throw new Error('Unexpected API path');
   }
   assert.equal(url.hostname,'localhost');
   const path=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
   assert.ok(!path.includes('..'));
   const types={js:'text/javascript',css:'text/css',html:'text/html',json:'application/json',svg:'image/svg+xml'};
   try{return route.fulfill({body:await readFile(dist+path),contentType:types[path.split('.').at(-1)]??'application/octet-stream'});}
   catch{return route.fulfill({status:404,body:''});}
  });
  await page.goto('http://localhost:5173/');
  const fli=page.getByRole('checkbox',{name:'Fli (Google Flights)',exact:true});
  await fli.waitFor();
  assert.equal(await fli.isChecked(),true);checks++;
  assert.equal(await fli.isEnabled(),true);checks++;
  await page.getByText('4 sources selected · Route/date combinations remain independent of source count.',{exact:true}).waitFor();checks++;
  const origin=page.getByRole('combobox',{name:'Origin airports',exact:true});
  const destination=page.getByRole('combobox',{name:'Destination airports',exact:true});
  await origin.fill('CGK');await origin.press('Enter');await origin.press('Escape');
  await destination.fill('HND');await destination.press('Enter');await destination.press('Escape');
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
  await page.getByText('P4.11 synthetic submission',{exact:true}).waitFor();
  assert.deepEqual(submissions[0].provider_ids,['skiplagged','swoop','octotrip','fli']);checks++;
  for(const name of ['Skiplagged','swoop (Google Flights)','OctoTrip']) await page.getByRole('checkbox',{name,exact:true}).uncheck();
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).click();
  await page.getByRole('button',{name:'Find cheapest flights',exact:true}).waitFor();
  assert.deepEqual(submissions[1].provider_ids,['fli']);checks++;
  assert.deepEqual(errors,[]);checks++;
  await context.close();
 }
 console.log(`P4.11 browser: ${checks} assertions passed`);
} finally {await browser.close();}
