const express = require('express')
const mongoose = require('mongoose')
const cheerio = require('cheerio')
const http = require('http')

const mongoURI = 'mongodb://localhost/db'

// Initializing
const app = express()

//Creating database
mongoose.connect(mongoURI)
db = mongoose.connection
db.on('error', console.error.bind(console, 'connection error:'))
db.once('open', function() {
    // If the connection was sucessful show:
    console.log('DB connection was sucessful')

    const Sounding = require('./dbmodels/sounding')

    //TODO:Verificar se os dados já estão lá e se não, enviar pro db
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
        });
      
        res.on('end', () => {
            const $ = cheerio.load(response)
            const tableRows = $('pre').html().split('\n').slice(4,-2)
            const tableData = tableRows.map(row => {
                const data = row.trim().split(/\s+/);
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
    
                newSoundingData.save()
                    .then(savedSounding => {
                        console.log('Sounding saved:', savedSounding);
                    })
                    .catch(error => {
                        console.error(error);
                    });
            }
        });
    }).on('error', (error) => {
        console.error(error);
    })

    console.log('DB ready')
});

module.exports = app