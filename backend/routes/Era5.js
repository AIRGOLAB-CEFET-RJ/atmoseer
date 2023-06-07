var express = require('express')
var router = express.Router()
const Era5 = require('../dbmodels/ERA5');
const { spawn } = require('child_process')
const fs = require("fs")
//const { netcdf } = require("netcdjs")

const nc_file = 'file.nc';  // Caminho para o arquivo .nc

//const process = spawn('python', ['python_scripts/save_ERA5.py'])
/*
process.on('exit', function(code) {
    console.log('child process exited with code ' + code.toString())
    fs.readFile("file.nc", (err, data) => {
        if (err) {
            console.error(err);
            return;
        }
        const reader = new NetCDFReader(data);
    }) 
    /*
    console.log('child process exited with code ' + code.toString())
    // Executando o programa Python
    spawn('python', ['python_scripts/send_ERA5.py']);*/
    // Ler o arquivo .nc
    /*
    const dataset = new netcdf.Dataset(nc_file);
    // Extrair os dados do arquivo .nc
    const dados = {};
    for (let var_name in dataset.variables) {
        const variable = dataset.variables[var_name];
        dados[var_name] = variable.slice();
    }

      for (let i = 0; i < dados.length; i++) {
        const dados = new Era5 ({
            geopotential: 
            relative_humidity: 
            temperature: 
            u_component_of_wind: 
            v_component_of_wind: 
            pressure_level: 
            year: 
            month: 
            day: 
            time:
          });

        // Criar uma instância do modelo 'Era5' e salvar no MongoDB
        const era5Instance = new Era5(era5Data);
        era5Instance.save()
        .then(savedEra5 => {
            console.log('Era5 saved:', savedEra5);
        })
        .catch(error => {
            console.error('Erro ao salvar Era5:', error);
        });
    }   */

//});

module.exports = router