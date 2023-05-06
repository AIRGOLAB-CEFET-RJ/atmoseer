const express = require('express')
const mongoose = require('mongoose')

const mongoURI = 'mongodb://127.0.0.1:27017/db' //'mongodb://localhost/db'

// Initializing
const app = express();

var era5Router = require('./routes/Era5');
var soundingRouter = require('./routes/Sounding');
var wsRouter = require('./routes/WeatherStation');

//Creating database
mongoose.connect(mongoURI)
db = mongoose.connection
db.on('error', console.error.bind(console, 'connection error:'))
db.once('open', function() {
    
   // app.use(express.static(path.join(__dirname, 'public')));

   app.use('/ERA5', era5Router );
   app.use('/sounding', soundingRouter);
   // app.use('/weatherstation', wsRouter);

});

module.exports = app