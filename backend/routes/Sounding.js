var express = require('express');
var router = express.Router();
const cheerio = require('cheerio')
const http = require('http')
const Sounding = require('../dbmodels/sounding');

function SoundingData() {
    let response = ''
    let date = new Date()
    let hour = (0).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false})
    if (date.getHours() >= 12) hour = 12

    http.get('http://weather.uwyo.edu/cgi-bin/sounding?region=samer&TYPE=TEXT%3ALIST&STNM=83746'+ 
    '&YEAR='+ date.getFullYear() + 
    '&MONTH='+ (date.getMonth() + 1) +
    '&FROM='+ date.getDate() + hour + 
    '&TO='+ date.getDate() + hour, (res) => {
        res.on('data', (chunk) => {
            response += chunk
        })
    
        res.on('end', () => {
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
            
            let time = Date.now()
            const soundingDataArray = []

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

            Sounding.insertMany(soundingDataArray)
            .then(savedSounding => {
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

setInterval(SoundingData, 12 * 60 * 60 * 1000)
SoundingData()

module.exports = router;