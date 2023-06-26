var express = require('express')
var router = express.Router()
const Era5 = require('../dbmodels/ERA5');
const { spawn } = require('child_process')
const fs = require("fs")
//const { netcdf } = require("netcdjs")

const nc_file = 'file.nc';  // Caminho para o arquivo .nc

//   ERA5 é um modelo muito grande e está atrasado pelo menos 4 dias. Está
// sendo enviado pro banco manualmente devido a sua demora. Caso troquem o
// modelo númerico para um mais atualizado, utilizar essa rota. 

module.exports = router