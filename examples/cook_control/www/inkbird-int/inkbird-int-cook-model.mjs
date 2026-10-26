// Inkbird INT optional dashboard presentation. All device communication stays in inkbird_int14.
const state = (s, id) => s[id]?.state;
const tr = (s, en, it) => state(s, 'input_select.bbq_language') === 'Italiano' ? it : en;
const valid = v => v != null && !['unknown', 'unavailable', '', 'none'].includes(v);
const num = v => valid(v) && Number.isFinite(Number(v)) ? Number(v) : null;
const escape = v => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const line = (v, muted = false) => `<div style="font:14px system-ui;line-height:1.5;text-align:left;white-space:normal;overflow-wrap:anywhere;letter-spacing:0;color:var(--${muted ? 'secondary' : 'primary'}-text-color)">${v}</div>`;
const degree = (v, f) => v == null ? '\u2014' : `${(f ? v * 9 / 5 + 32 : v).toFixed(1)}\u00b0${f ? 'F' : 'C'}`;
function celsius(s, id) {
  const v = num(state(s, id));
  return v === null ? null : s[id]?.attributes?.unit_of_measurement === '\u00b0F' ? (v - 32) * 5 / 9 : v;
}

export function connection(s, prefix, now = Date.now()) {
  const packets = [['Bluetooth', 'last_ble_update_epoch'], [tr(s,'Local Wi-Fi','Wi-Fi locale'), 'last_lan_update_epoch']]
    .map(([label, key]) => ({label, epoch:num(state(s, `${prefix}_${key}`))}))
    .filter(p => p.epoch > 0 && p.epoch <= now / 1000 + 60).sort((a,b) => b.epoch - a.epoch);
  const packet = packets[0];
  const age = packet ? Math.max(0, Math.floor(now / 1000 - packet.epoch)) : null;
  const fresh = age !== null && age <= 120;
  const ble = state(s, `${prefix.replace('sensor.', 'binary_sensor.')}_ble_connected`) === 'on';
  return {age, fresh, label:packet?.label || tr(s,'No local data','Nessun dato locale'), status:!fresh ? tr(s,'Stale readings','Dati non recenti') : packet.label === 'Bluetooth' && !ble ? tr(s,'Between BLE readings','Tra due letture BLE') : tr(s,'Recent readings','Dati recenti')};
}

export function renderConnection(s, prefix, now) {
  const c = connection(s, prefix, now);
  const battery = num(state(s, `${prefix}_base_battery`));
  return line(`<b>${c.label}</b> &middot; ${c.status} &middot; ${c.age === null ? '\u2014' : c.age + tr(s,' s ago',' s fa')}`)
    + line(`${tr(s,'Station battery','Batteria station')}: ${battery === null ? '\u2014' : battery + '%'}`, true);
}

export function renderSide(s, prefix, n, now) {
  const f = (state(s, 'input_select.inkbird_unit') || '').includes('F');
  const target = num(state(s, `input_number.inkbird_target_${n}`));
  const alarm = celsius(s, `${prefix}_probe_${n}_target_high_temperature`);
  const ambient = celsius(s, `${prefix}_probe_${n}_ambient_temperature`);
  const enabled = state(s, `input_boolean.bbq_probe_${n}_enabled`) === 'on';
  const fresh = connection(s, prefix, now).fresh;
  const battery = num(state(s, `${prefix}_probe_${n}_battery`));
  const suspect = state(s, `${prefix.replace('sensor.', 'binary_sensor.')}_probe_battery_report_suspect`) === 'on';
  return line(`<b>${tr(s,'Ambient','Ambiente')} ${degree(ambient, f)}</b>`)
    + line(`${tr(s,'HA target','Soglia HA')}: ${target > 0 ? degree(target, f) : tr(s,'not set','non impostata')}`)
    + line(`${tr(s,'Station alarm','Allarme station')}: ${degree(alarm, f)}`, true)
    + line(!fresh ? tr(s,'Last reading, not live','Ultima lettura, non live') : enabled ? tr(s,'Alerts on','Avvisi attivi') : tr(s,'Alerts off','Avvisi disattivati'), true)
    + line(`${tr(s,'Battery','Batteria')}: ${battery === null ? '\u2014' : battery + '%'}${suspect ? tr(s,' (suspect report)',' (dato sospetto)') : ''}`, true);
}

export function renderHeader(s, prefix, n) {
  const name = state(s, `input_text.inkbird_name_${n}`);
  const value = state(s, `sensor.bbq_probe_${n}_status`);
  const labels = {heating:tr(s,'Below target','Sotto soglia'),close:tr(s,'Near target','Vicino alla soglia'),ready:tr(s,'HA target reached','Soglia raggiunta'),idle:tr(s,'Not armed','Non attiva')};
  const label = state(s, `input_boolean.bbq_probe_${n}_enabled`) !== 'on' ? tr(s,'Alerts off','Avvisi disattivati')
    : connection(s,prefix).fresh ? labels[value] || tr(s,'No reading','Nessuna lettura') : tr(s,'Last reading','Ultima lettura');
  return line(`<b>P${n} &nbsp; ${escape(valid(name) ? name : `${tr(s,'Probe','Sonda')} ${n}`)}</b>`) + line(label,true);
}

export function renderSummary(s) {
  const n = state(s, 'input_select.inkbird_active_probe');
  const voiceOn = state(s, 'input_boolean.bbq_tts_alerts') === 'on';
  const engine = state(s, 'input_select.bbq_tts_engine');
  const speaker = state(s, 'input_select.bbq_tts_speaker');
  const available = valid(speaker) && valid(state(s, speaker)) && (engine === 'Alexa (native)' || valid(state(s, engine)));
  const voice = !voiceOn ? tr(s,'off','spenta') : available ? escape(s[speaker]?.attributes?.friendly_name || speaker) : tr(s,'not configured or unavailable','non configurata o non disponibile');
  const tv = state(s, 'input_boolean.bbq_tv_alerts') === 'on' ? tr(s,'TV text on','testo TV attivo') : tr(s,'TV text off','testo TV spento');
  return line(`<b>${tr(s,'Preset probe','Sonda preset')} ${escape(valid(n) ? n : '\u2014')}</b> &middot; ${tr(s,'Voice','Voce')}: ${voice} &middot; ${tv}`);
}

export function renderDiagram(s, prefix, n) {
  const f = (state(s, 'input_select.inkbird_unit') || '').includes('F');
  return line(`<b>${tr(s,'Food','Cuore')} ${degree(celsius(s, `${prefix}_probe_${n}_internal_temperature`), f)}</b>`)
    + '<svg aria-label="INT-14-BW: food at tip, ambient at handle" role="img" viewBox="0 0 420 70" style="display:block;width:100%;height:70px"><path d="M18 38 L45 31 H300 V45 H45 Z" fill="#c7cdd1" stroke="#77838d"/><rect x="300" y="23" width="100" height="30" rx="5" fill="#25292b"/><circle cx="45" cy="38" r="5" fill="#278acc"/><circle cx="385" cy="38" r="5" fill="#d69d20"/></svg>'
    + line(`<span style="float:right">${tr(s,'Ambient','Ambiente')} ${degree(celsius(s, `${prefix}_probe_${n}_ambient_temperature`), f)}</span>`, true);
}

const expression = js => `[[[ return ${js}; ]]]`;
function info(js) {
  return {type:'custom:button-card', show_name:false, show_icon:false, triggers_update:'all', tap_action:{action:'none'},
    styles:{card:[{padding:'16px'}, {'border-radius':'8px'}], grid:[{'grid-template-areas':'"info"'}, {'grid-template-columns':'minmax(0,1fr)'}]}, custom_fields:{info:expression(js)}};
}

export function adapt(input, config) {
  const result = structuredClone(input);
  const prefix = config.prefix;
  if (!/^sensor\.[a-z0-9_]+$/.test(prefix)) throw new Error('Invalid Inkbird prefix');
  const q = JSON.stringify(prefix);
  const it = config.language === 'it';
  const label = (en, italian) => it ? italian : en;
  const template = result.button_card_templates.inkbird_probe;
  template.custom_fields.header = expression(`window.InkbirdIntCookControl.renderHeader(states, ${q}, variables.num)`);
  template.custom_fields.side = expression(`window.InkbirdIntCookControl.renderSide(states, ${q}, variables.num)`);
  template.styles.grid = [{'grid-template-areas':'"header header header" "fig gauge side" "spark spark spark"'},
    {'grid-template-columns':'24px 128px minmax(0,1fr)'}, {'grid-template-rows':'auto minmax(150px,auto) 66px'}, {'gap':'8px'}];
  template.styles.custom_fields.side.push({'min-width':'0'});
  template.styles.card.push({'border-radius':'8px'});
  for (const item of Object.values(result.button_card_templates)) {
    if (item.styles?.card) item.styles.card.push({'border-radius':'8px'});
  }
  const names = {'Cook Control':'Cottura','Probes':'Sonde','Settings':'Impostazioni',
    'Recepten':'Preset', 'Internal':'Cuore', 'Internal - control':'Cuore', 'Ambient':'Ambiente', 'Speaker':'Altoparlante',
    'Battery':'Batteria', 'Rate':'Variazione', 'Target':'Soglia HA', 'Last hour':'Ultima ora',
    'Voice engine / Alexa native':'Voce / Alexa nativa', 'Spoken announcements':'Annunci vocali',
    'TV text notifications':'Avvisi testuali TV', 'TV media player entity':'TV: entita media player',
    'TV notify service (without notify.)':'TV: servizio notify senza prefisso',
    'Test notification':'Prova Echo e TV', 'Refresh devices':'Aggiorna dispositivi',
    'Alerts and announcements':'Avvisi e annunci', 'Active probe':'Sonda preset'};
  function walk(node) {
    if (Array.isArray(node)) return node.map(walk);
    if (!node || typeof node !== 'object') return node;
    if (node.type === 'picture-elements') {
      const entity = node.elements?.find(e => e.entity?.endsWith('_internal_temperature'))?.entity;
      const match = entity?.match(/_probe_(\d)_internal_temperature$/);
      if (match) return info(`window.InkbirdIntCookControl.renderDiagram(states, ${q}, ${match[1]})`);
    }
    for (const key of ['name','title','heading']) {
      if (!Object.hasOwn(node, key)) continue;
      if (it && names[node[key]]) node[key] = names[node[key]];
      else if (!it) node[key] = ({Recepten:'Presets','Internal - control':'Food',Internal:'Food',Target:'HA target'})[node[key]] || node[key];
    }
    if (node.type === 'custom:button-card' && node.custom_fields?.title && node.custom_fields?.status) {
      node.triggers_update = 'all';
      node.custom_fields.title = `<div style="text-align:left;font:600 20px system-ui">Cook Control</div><div style="text-align:left;font:14px system-ui">INT-14-BW &middot; ${label('4 probes, 8 temperatures','4 sonde, 8 temperature')}</div>`;
      node.custom_fields.status = expression(`window.InkbirdIntCookControl.renderConnection(states, ${q})`);
      node.styles.card.push({'border-radius':'8px'});
    }
    if (node.type === 'conditional' && node.conditions?.some(c => c.entity === 'sensor.bbq_alert_count')) return info('window.InkbirdIntCookControl.renderSummary(states)');
    if (node.type === 'grid' && node.cards?.some(c => c.template === 'inkbird_probe'))
      node.card_mod = {style:'#root { grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr)) !important; }'};
    if (node.type === 'history-graph' && node.hours_to_show === 12) {
      node.title = label('Probe 1: food and ambient','Sonda 1: cuore e ambiente');
      node.entities = [{entity:`${prefix}_probe_1_internal_temperature`,name:label('Food','Cuore')}, {entity:`${prefix}_probe_1_ambient_temperature`,name:label('Ambient','Ambiente')}];
    }
    if (node.type === 'markdown' && node.content?.startsWith('#### Recipe presets')) node.content = label('### HA presets','### Preset HA');
    if (node.variables?.note === 'Food-safe') node.variables.note = label('HA preset','Preset HA');
    if (node.tap_action?.data?.tag === 'inkbird_test') Object.assign(node.tap_action.data, {
      title:label('BBQ notification test','Prova avvisi BBQ'), message:label('Cook Control notification test.','Prova avvisi Cook Control.'),
      tts_message:label('Barbecue announcement test.','Prova annuncio barbecue.')});
    if (node.type === 'entities' && node.entities?.some(e => e.entity === 'input_boolean.bbq_tts_alerts')) {
      node.entities.unshift({entity:'input_select.bbq_language',name:label('Language','Lingua')}, ...[1,2,3,4].map(n => ({entity:`input_boolean.bbq_probe_${n}_enabled`,name:`${label('Probe alerts','Avvisi sonda')} ${n}`})));
    }
    for (const key of Object.keys(node)) node[key] = walk(node[key]);
    return node;
  }
  result.views = walk(result.views);
  const settings = result.views.find(v => v.path === 'settings');
  if (settings?.header?.card) settings.header.card.content = label('## Settings','## Impostazioni');
  const cook = result.views.find(v => v.path === 'cook');
  cook?.sections?.[0]?.cards.push({type:'grid',title:label('Probe alerts','Avvisi sonde'),columns:2,square:false,
    cards:[1,2,3,4].map(n=>({type:'tile',entity:`input_boolean.bbq_probe_${n}_enabled`,name:`P${n}`,hide_state:true,
      features:[{type:'toggle'}],features_position:'inline',tap_action:{action:'none'},icon_tap_action:{action:'toggle'}}))});
  return result;
}
