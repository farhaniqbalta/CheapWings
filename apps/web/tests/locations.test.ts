import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createLocationService } from "../src/lib/locations.ts";
import { planScope } from "../src/lib/scope.ts";
const catalog = JSON.parse(readFileSync(new URL('../public/locations.json',import.meta.url),'utf8'));
const service = createLocationService(catalog);
test('physical code is first; metro is typed; accent and aliases match', () => {
  assert.equal(service.search('cGk')[0]?.id,'airport:CGK');
  assert.equal(service.search('TYO')[0]?.type,'city');
  assert.ok(service.search('Sao Paulo').some(e=>e.code==='GRU'));
  assert.ok(service.search('Haneda').some(e=>e.code==='HND'));
  assert.ok(service.search('日本').some(e=>e.id==='country:JP'));
});
test('country/city browsing never becomes an airport suggestion or collapsed ambiguity', () => {
  assert.ok(service.search('', 'country:JP').every(e=>e.type==='airport'));
  assert.deepEqual(service.search('', 'metro:JP:TYO').map(e=>e.code).sort(),['HND','NRT']);
  const cities=service.search('Springfield').filter(e=>e.type==='city');
  assert.ok(cities.length>1);
  assert.equal(new Set(cities.map(e=>e.id)).size,cities.length);
  assert.deepEqual(service.search('HND','missing'),[]);
});
test('major mappings are explicit, reproducible and have no fallback',()=>{
  assert.deepEqual(service.resolve('metro:JP:TYO')?.codes,['HND','NRT']);
  assert.deepEqual(service.resolve('country:JP'),service.resolve('country:JP'));
  assert.equal(service.resolve('country:US'),null);
  assert.equal(service.resolve('airport:HND'),null);
  assert.equal(service.resolve('missing'),null);
  assert.equal(service.resolve('country:JP')?.selection.catalog_version,catalog.version);
});
test('web and backend snapshots are byte-identical',()=>{
  assert.equal(readFileSync(new URL('../public/locations.json',import.meta.url),'utf8'),
    readFileSync(new URL('../../../backend/src/cheapwings/locations/catalog.json',import.meta.url),'utf8'));
});
test('scope counts valid deduplicated pairs, dates, providers and zero routes',()=>{
  const p=planScope(['MEL','mel','DPS'],['DPS'],'2027-01-01','2027-04-30',['a','a','b']);
  assert.deepEqual(p,{days:120,pairs:1,combinations:120,providerCount:2,estimatedWorkItems:240});
  assert.equal(planScope(['MEL','DPS'],['DPS'],'2027-01-01','2027-05-01',[]).combinations,121);
  assert.equal(planScope(['HND'],['HND'],'2027-01-01','2027-01-03',[]).combinations,0);
  assert.equal(planScope(['MEL'],['DPS'],'2027-01-03','2027-01-01',[]).combinations,0);
  assert.equal(planScope(['MEL'],['DPS'],'','',[]).combinations,0);
});
