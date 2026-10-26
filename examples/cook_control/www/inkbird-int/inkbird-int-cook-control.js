import './cook-base-v1.4.3.js?v=1';
import * as presentation from './inkbird-int-cook-model.mjs?v=1.0.4';

window.InkbirdIntCookControl = Object.freeze({...presentation});
const Base = customElements.get('ll-strategy-dashboard-inkbird-int-cook-base');

class InkbirdIntCookControl extends HTMLElement {
  static getCreateSuggestions() { return {title:'Inkbird Cook Control',icon:'mdi:grill'}; }
  static shouldRegenerate(config, oldHass, newHass) {
    return ['input_text.inkbird_sensor_prefix','input_select.bbq_language'].some(
      id => oldHass.states[id]?.state !== newHass.states[id]?.state);
  }
  static async generate(config, hass) {
    if (!hass.states['input_text.inkbird_sensor_prefix']) {
      throw new Error('Install the Cook Control YAML package and restart Home Assistant before opening this dashboard.');
    }
    const configured = hass.states['input_text.inkbird_sensor_prefix']?.state;
    const candidates = Object.keys(hass.states).filter(id => id.endsWith('_configured_model_profile') && hass.states[id].state === 'int14_bw')
      .map(id => id.replace(/_configured_model_profile$/, ''));
    const prefix = config.prefix || (/^sensor\.[a-z0-9_]+$/.test(configured || '') ? configured : candidates.length === 1 ? candidates[0] : '');
    config = {...config, prefix, model:config.model || 'int14_bw', language:hass.states['input_select.bbq_language']?.state === 'Italiano' ? 'it' : 'en'};
    if (config.model !== 'int14_bw' || !/^sensor\.[a-z0-9_]+$/.test(prefix)) {
      throw new Error('Cook Control requires an INT-14-BW. If more than one station is present, set prefix in the dashboard configuration. See the setup guide.');
    }
    const actual = hass.states[`${config.prefix}_configured_model_profile`]?.state;
    if (actual && !['unknown', 'unavailable', 'int14_bw'].includes(actual)) {
      throw new Error('This Cook Control preview is validated for INT-14-BW only.');
    }
    const channels = [1,2,3,4].flatMap(n => ['internal','ambient'].map(c => `${config.prefix}_probe_${n}_${c}_temperature`));
    if (!channels.every(id => id in hass.states)) {
      throw new Error('The eight INT-14-BW temperature entities were not found. Check the prefix and enable the food/ambient entities.');
    }
    if (configured !== prefix) {
      const it = config.language === 'it';
      return {title:'Cook Control',views:[{title:it ? 'Termometro' : 'Thermometer',path:'setup',cards:[
        {type:'markdown',content:`## Inkbird INT-14-BW\n\n\`${prefix}\``},
        {type:'button',name:it ? 'Usa questo termometro' : 'Use this thermometer',icon:'mdi:thermometer-check',tap_action:{action:'perform-action',perform_action:'input_text.set_value',target:{entity_id:'input_text.inkbird_sensor_prefix'},data:{value:prefix}}},
        {type:'entities',entities:['input_select.bbq_language']},
      ]}]};
    }
    return presentation.adapt(await Base.generate(config, hass), config);
  }
}

customElements.define('ll-strategy-dashboard-inkbird-int-cook-control', InkbirdIntCookControl);
window.customStrategies = window.customStrategies || [];
window.customStrategies.push({type:'inkbird-int-cook-control',strategyType:'dashboard',name:'Inkbird Cook Control',description:'INT-14-BW: food, ambient and cooking alerts',documentationURL:'https://github.com/zampix1/ha-inkbird-int14/blob/main/examples/cook_control/README.md'});
