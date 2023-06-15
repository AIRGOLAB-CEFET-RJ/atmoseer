var express = require('express');
var router = express.Router();
const https = require('https');
const Inmet = require('../dbmodels/Inmet');
const token = require('./token');

function InmetData() {
    let INMET_STATION_CODES_RJ = ['A636', 
                          'A621', 
                          'A602', 
                          'A652',
                          'A627']
    let date = new Date()

    INMET_STATION_CODES_RJ.forEach(code => {
        let response = ''
        let url = 'https://apitempo.inmet.gov.br/token/estacao/'+
                    date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate() + '/'+
                    date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate() + '/'+
                    code + '/' + token
        console.log(url)

        https.get(url, (res) => {
            res.on('data', (chunk) => {
                response += chunk
            })

            res.on('end', () => {
                jsonData = JSON.parse(response)
                
                const inmetDataArray = []

                for (let i = 0; i < jsonData.length; i++) {
                    const newInmetData = new Inmet( {
                        VEN_DIR: jsonData[i].VEN_DIR,
                        CHUVA: jsonData[i].CHUVA,
                        PRE_INS: jsonData[i].PRE_INS,
                        PRE_MIN: jsonData[i].PRE_MIN,
                        UMD_MAX: jsonData[i].UMD_MAX,
                        PRE_MAX: jsonData[i].PRE_MAX,
                        VEN_VEL: jsonData[i].VEN_VEL,
                        PTO_MIN: jsonData[i].PTO_MIN,
                        TEM_MAX: jsonData[i].TEM_MAX,
                        RAD_GLO: jsonData[i].RAD_GLO,
                        PTO_INS: jsonData[i].PTO_INS,
                        VEN_RAJ: jsonData[i].VEN_RAJ,
                        TEM_INS: jsonData[i].TEM_INS,
                        UMD_INS: jsonData[i].UMD_INS,
                        TEM_MIN: jsonData[i].TEM_MIN,
                        UMD_MIN: jsonData[i].UMD_MIN,
                        PTO_MAX: jsonData[i].PTO_MAX
                    })
                    
                    inmetDataArray.push(newInmetData)
                }

                Inmet.insertMany(inmetDataArray)
                .then(savedInmet => {
                    console.log('Dados do Inmet salvos no MongoDB com sucesso.')
                })
                .catch(error => {
                    console.error('Erro ao salvar dados do Inmet no MongoDB:', error)
                })
            })
        }).on('error', (error) => {
            console.error(error)
        })
    })
}

setInterval(InmetData, 1 * 60 * 60 * 1000)
InmetData()

module.exports = router;