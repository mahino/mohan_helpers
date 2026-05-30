


const express = require('express');
const app = express();
const port = 3001;
require('dotenv').config();
app.set('view engine', 'ejs');

const Influx = require('influx');
const influx = new Influx.InfluxDB({
  host: '10.48.212.161', 
  database: 'api_latencies_final' 
});

const statsForOptions = ['calm','epsilon','domain_manager', 'pc_vm', 'load_average'];
const percentileOptionsValues = ['perc_90','perc_95', 'perc_99'];
app.get('/', async (req, res) => {
  try {
    const apiNames = await influx.query(`show tag values from api_latencies with key = api_name`);
    const caVersions = await influx.query(`show tag values from api_latencies with key = calm_version`);
    const nodeConfigs = await influx.query(`show tag values from api_latencies with key = node_config`);
    const caVersionOptions = caVersions.map(version => version.value);
    const apiNameOptions = apiNames.map(name => name.value);
    const nodeConfigOptions = nodeConfigs.map(config => config.value);
    const statsTypeOptions = ['perc90','max','avg'];
    res.render('index', { caVersions: caVersionOptions.sort((a, b) => b.localeCompare(a)), apiNames: apiNameOptions, nodeConfigs: nodeConfigOptions, percentiles: percentileOptionsValues, statsType: statsTypeOptions, statsFor: statsForOptions});
  } 
  catch (error) {
    console.error('Error fetching dropdown values:', error);
    res.status(500).send('Internal server error');
  }
});

app.get('/data', async (req, res) => {
  try {
    const { ca_version, api_name, node_config, percentile, stats_toggle, stats_for } = req.query;
    const apiName = api_name.replace(/,/g, '|');
    const calmVersions = ca_version.split(",");
    const percentileValues = percentile.split(",");
    // const statsFor = stats_for.replace(/,/g, '|');
    const statsFor = stats_for.split(",");
    const api_latencies = [];
    const app_count_data = [];
    const calm_versions = [];
    const other_data = [];
    const others_ids_data = [];
    const stats_ids_data = [];
    const system_stats = [];
    const trueValues = statsForOptions.filter((_, index) => statsFor[index] === 'true').join('|');
    const percentileOptions = percentileOptionsValues.filter((_, index) => percentileValues[index] === 'true')

    for (let calmVerison = 0; calmVerison < calmVersions.length; calmVerison++) {
      query = `SELECT * FROM "api_latencies" WHERE "api_name" =~ /^(${apiName})$/ AND "calm_version" = '${calmVersions[calmVerison]}' AND "node_config" = '${node_config}'`
      const api_latencies_result = await influx.query(query);
      const entity_count_ids = api_latencies_result.map(point => point.entities_count_id)
      stats_ids_data.push(api_latencies_result.map(point => point.stats_id)[0])
      others_ids_data.push(api_latencies_result.map(point => point.others_id)[0])
      calm_versions.push(api_latencies_result.map(point => point.calm_version)[0])
      const mySet = new Set(entity_count_ids);
      const uniqueList = Array.from(mySet);
      let transformedData = {};
      api_latencies_result.forEach(item => {
        let { api_name, method } = item;
          transformedData[api_name] = {'percLatencies': percentileOptions.map(key => item[key]), 'method': method};
      })
      const data = {
        api_latencies: transformedData
      };
      if ( uniqueList.length == 1) {
        entity_query = `select * from entity_count where (entity_count_id='${uniqueList[0]}' AND "calm_version" = '${calmVersions[calmVerison]}' AND "node_config" = '${node_config}')`
        entity_result = await influx.query(entity_query);
        app_count_data.push(entity_result.map(point => point.applications)[0])
      } else {
        throw new Error('ERROR: Found multi-ids for entity_count');
      }
      api_latencies.push(data);
    };
    if (stats_toggle === 'true') {
      test_result = await influx.query(`SHOW FIELD KEYS FROM system_stats`);
      const cpuMemFieldKeysmap = test_result.map( field => field.fieldKey);
      const regex = new RegExp(trueValues);
      const cpuMemFieldKeys = cpuMemFieldKeysmap.filter(field => regex.test(field));
      for (let statCount = 0 ; statCount < stats_ids_data.length ; statCount++) {
        entity_query = `select ${cpuMemFieldKeys.join(',')} from system_stats where ( "calm_version" = '${calmVersions[statCount]}' AND "node_config" = '${node_config}')`
        entity_result = await influx.query(entity_query);
        system_stats.push(entity_result[0]);
      }
    };
    if (stats_toggle === 'true') {
      for (let otherCount = 0 ; otherCount < others_ids_data.length ; otherCount++) {
        entity_query = `select * from others where (others_id='${others_ids_data[otherCount]}' AND "calm_version" = '${calmVersions[otherCount]}' AND "node_config" = '${node_config}')`
        entity_result = await influx.query(entity_query);
        other_data.push(entity_result[0]);
      }
    };
    query = `show tag values from api_latencies with key = api_name`
    const api_names_data = await influx.query(query);
    const api_names = api_names_data.map(version => version.value);
    data = {api_latencies_data: api_latencies, system_stats:system_stats, api_names: api_names, percentiles: percentileOptions, calm_versions:calm_versions, app_count_data:app_count_data, others_data:other_data}
    console.log(JSON.stringify(data))
    res.json(data);
  } catch (error) {
    console.error('Error fetching data from InfluxDB:', error);
    res.status(500).json({ error: 'Error fetching data from InfluxDB' });
  }
});

app.listen(port, () => {
  console.log(`Server is listening at http://localhost:${port}`);
});





