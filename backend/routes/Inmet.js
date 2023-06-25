var express = require('express');
var router = express.Router();

//Importando Https: Biblioteca necessária para fazer a requisição https
const https = require('https');

//Importando o schema do mongodb do Inmet
const Inmet = require('../dbmodels/Inmet');

//Importando o token: Necessário criar um arquivo token.js com uma const do token do Inmet
const token = require('./token');

//Função InmetData: Envia uma requisição https GET para pegar os JSONs de cada estação do Inmet
function InmetData() {

    //Código das estações do Inmet
    let INMET_STATION_CODES_RJ = ['A636', 
                          'A621', 
                          'A602', 
                          'A652',
                          'A627']

    //Pega a data atual e zera os minutos e segundos
    let date = new Date()
    date.setMinutes("0")
    date.setSeconds("0")

    INMET_STATION_CODES_RJ.forEach(code => {
        let response = ''
        //Monta a url que será enviada a requisição
        let url = 'https://apitempo.inmet.gov.br/token/estacao/'+
                    date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate() + '/'+
                    date.getFullYear() + '-' + (date.getMonth() + 1) + '-' + date.getDate() + '/'+
                    code + '/' + token

        https.get(url, (res) => {
            res.on('data', (chunk) => {
                response += chunk
            })

            res.on('end', () => {
                jsonData = JSON.parse(response)
                
                const inmetDataArray = []

                for (let i = 0; i < jsonData.length; i++) {
                    //Pega a data anteriormente definida e coloca a hora de medição registrada no JSON da estação
                    date.setHours(jsonData[i].HR_MEDICAO.substr(0, 2))
                    
                    //Armazena os dados do JSON da estação em um objeto Inmet, incluindo seu código e tempo da consulta em formato datetime
                    const newInmetData = new Inmet( {
                        COD_ESTACAO: code,
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
                        PTO_MAX: jsonData[i].PTO_MAX,
                        TIME: date
                    })
                    
                    inmetDataArray.push(newInmetData)
                }

                //Salva os dados no mongodb
                Inmet.insertMany(inmetDataArray)
                .then(() => {
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

//A função InmetData será executada a cada 1 hora
setInterval(InmetData, 1 * 60 * 60 * 1000)
InmetData()

module.exports = router;