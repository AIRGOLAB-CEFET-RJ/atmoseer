const mongoose = require('mongoose')
const Schema = mongoose.Schema

const corSchema = new Schema ({
    precipitation: { type: Number, required: true },
    wind_dir: { type: Number, required: true },
    wind_speed: { type: Number, required: true },
    temperature: { type: Number, required: true },
    pressure: { type: Number, required: true },
    humidity: { type: Number, required: true },
    station: { type: String, required: true },
    datetime: { type: Date, required: true }
})

const COR = mongoose.model('COR', corSchema)

module.exports = COR