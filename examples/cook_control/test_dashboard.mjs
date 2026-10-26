import assert from 'node:assert/strict';

const registry = new Map();
globalThis.HTMLElement = class {};
globalThis.customElements = {get:name=>registry.get(name),define:(name,cls)=>registry.set(name,cls)};
globalThis.window = {};
await import('./www/inkbird-int/inkbird-int-cook-control.js');
const Strategy = registry.get('ll-strategy-dashboard-inkbird-int-cook-control');
const prefix = 'sensor.test_inkbird';
const config = {prefix,model:'int14_bw'};
const states = {'input_text.inkbird_sensor_prefix':{state:prefix}, 'input_select.bbq_language':{state:'English'}};
for (let n=1;n<=4;n++) for (const channel of ['internal','ambient']) {
  states[`${prefix}_probe_${n}_${channel}_temperature`] = {state:'22',attributes:{unit_of_measurement:'\u00b0C'}};
}
const result = await Strategy.generate(config,{states});
assert.equal(result.inkbird_model,'int14_bw');
const probes = JSON.stringify(result.views.find(v=>v.path==='probes'));
assert.doesNotMatch(probes,/food_[1-4]_temperature|picture-elements/);
for (const id of Object.keys(states).filter(id=>id.startsWith(prefix))) assert.ok(probes.includes(id));
function styleCheck(node) {
  if (!node || typeof node !== 'object') return;
  if (node.styles) for (const [key,value] of Object.entries(node.styles)) {
    for (const rules of key === 'custom_fields' ? Object.values(value) : [value]) {
      assert.ok(Array.isArray(rules));
      assert.ok(rules.every(rule=>rule && typeof rule === 'object' && !Array.isArray(rule)));
    }
  }
  Object.values(node).forEach(styleCheck);
}
styleCheck(result);
await assert.rejects(Strategy.generate({...config,model:'int14s_bw'},{states}),/requires/);
await assert.rejects(Strategy.generate({...config,prefix:'invalid'},{states}),/requires/);
await assert.rejects(Strategy.generate(config,{states:{}}),/YAML package/);
await assert.rejects(Strategy.generate(config,{states:{'input_text.inkbird_sensor_prefix':{state:prefix}}}),/eight/);
await assert.rejects(Strategy.generate(config,{states:{...states,[`${prefix}_configured_model_profile`]:{state:'int14s_bw'}}}),/only/);
assert.equal(registry.has('ll-strategy-dashboard-inkbird-bbq'),false);
console.log('Cook Control preview: 8 channels, valid styles, model guards and isolated strategy registration passed.');
const detected = {...states, [`${prefix}_configured_model_profile`]:{state:'int14_bw'}};
assert.equal((await Strategy.generate({}, {states:detected})).inkbird_model,'int14_bw');
detected['input_text.inkbird_sensor_prefix'] = {state:''};
const setup = await Strategy.generate({}, {states:detected});
assert.equal(setup.views[0].path,'setup');
assert.equal(setup.views[0].cards[1].tap_action.data.value,prefix);
assert.ok(Strategy.shouldRegenerate({}, {states}, {states:{...states,'input_select.bbq_language':{state:'Italiano'}}}));
const {connection,renderDiagram,renderHeader} = window.InkbirdIntCookControl;
const now = Date.now();
const recent = {...states,[`${prefix}_last_ble_update_epoch`]:{state:String(now/1000-10)}};
assert.equal(connection(recent,prefix,now).fresh,true);
assert.equal(connection({...recent,[`${prefix}_last_ble_update_epoch`]:{state:String(now/1000-121)}},prefix,now).fresh,false);
assert.equal(connection({...states,[`${prefix}_last_cloud_update_epoch`]:{state:String(now/1000)}},prefix,now).fresh,false);
assert.equal((renderDiagram(recent,prefix,1).match(/<circle /g)||[]).length,2);
assert.match(renderHeader(recent,prefix,1),/Alerts off/);
assert.match(renderHeader({...recent,'input_select.bbq_language':{state:'Italiano'}},prefix,1),/Avvisi disattivati/);
console.log('One-time setup, language regeneration, freshness and two-sensor diagram passed.');
