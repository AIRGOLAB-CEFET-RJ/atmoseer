var express = require('express');
var router = express.Router();

//Importando cheerio: Biblioteca necessária para o webscraping dos dados vindo da requisição http
const cheerio = require('cheerio')

//Importando Http: Biblioteca necessária para fazer a requisição http
const http = require('http')

//Importando o schema do mongodb da Radiossonda
const Sounding = require('../dbmodels/Sounding');

//Função InmetData: Envia uma requisição http GET para pegar os dados da radiossonda
function SoundingData() {
    let response = ''

    //Pega a data atual
    let date = new Date()

    //Cria a variável hour formatada em 2 dígitos e, se for maior ou igual a 12, a hora é substituída por 12
    let hour = (0).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false})
    if (date.getHours() >= 12) hour = 12

    //Monta a url que será enviada a requisição
    http.get('http://weather.uwyo.edu/cgi-bin/sounding?region=samer&TYPE=TEXT%3ALIST&STNM=83746'+ 
    '&YEAR='+ date.getFullYear() + 
    '&MONTH='+ (date.getMonth() + 1) +
    '&FROM='+ date.getDate() + hour + 
    '&TO='+ date.getDate() + hour, (res) => {
        res.on('data', (chunk) => {
            response += chunk
        })
    
        res.on('end', () => {
            //Faz o webscraping do html retornado pela requisição pegando os valores relevantes da radiossonda e os armazenando em tableData
            const $ = cheerio.load(response)
            const tableRows = $('pre').html().split('\n').slice(4,-2)
            const tableData = tableRows.map(row => {
                const data = row.trim().split(/\s+/)
                return {
                    PRES: data[0],
                    HGHT: data[1],
                    TEMP: data[2],
                    DWPT: data[3],
                    RELH: data[4],
                    MIXR: data[5],
                    DRCT: data[6],
                    SKNT: data[7],
                    THTA: data[8],
                    THTE: data[9],
                    THTV: data[10]
                };
            });
            
            //Pega a hora atual
            let time = Date.now()
            const soundingDataArray = []

            //Armazena os dados de tableData em um objeto Sounding, incluindo o tempo da consulta em formato datetime
            for (let i = 0; i < tableData.length; i++) {
                const newSoundingData = new Sounding( {
                    pressure: tableData[i].PRES,
                    height: tableData[i].HGHT,
                    temperature: tableData[i].TEMP,
                    dewpoint: tableData[i].DWPT,
                    direction: tableData[i].DRCT,
                    speed: tableData[i].SKNT,
                    time: time
                })
                
                soundingDataArray.push(newSoundingData)
            }
            
            //Salva os dados no mongodb
            Sounding.insertMany(soundingDataArray)
            .then(() => {
                console.log('Dados da sonda salvos no MongoDB com sucesso.')
            })
            .catch(error => {
                console.error('Erro ao salvar dados da sonda no MongoDB:', error)
            })
        })
    }).on('error', (error) => {
        console.error(error)
    })
}

//A função InmetData será executada a cada 12 horas
setInterval(SoundingData, 12 * 60 * 60 * 1000)
SoundingData()

module.exports = router;