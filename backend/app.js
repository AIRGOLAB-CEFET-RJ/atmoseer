const express = require('express')
const mongoose = require('mongoose')

const mongoURI = 'mongodb://127.0.0.1:27017/db' //'mongodb://localhost/db'

// Initializing
const app = express()

app.listen(3000, () => {
   console.log('Listening for request on port 3000');
});

const soundingRouter = require('./routes/Sounding')
const corRouter = require('./routes/COR')
const inmetRouter = require('./routes/Inmet')
//const era5Router = require('./routes/Era5')

app.use('/sounding', soundingRouter)
app.use('/cor', corRouter)
app.use('/inmet', inmetRouter)
//app.use('/era5', era5Router)

mongoose.connect(mongoURI)
db = mongoose.connection
db.on('error', console.error.bind(console, 'connection error:'))

module.exports = app