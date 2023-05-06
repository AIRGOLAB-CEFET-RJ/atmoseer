const mongoose = require('mongoose')
const Schema = mongoose.Schema

const wsSchema = new Schema ({
    Dia: {
        type: Date,
        required: true,
        default: 0
    },
    Hora: {
        type: Number,
        required: true,
        default: 0
    },
    HBV: {
        type: Number,
        required: true,
        default: 0
    },
    Chuva: {
        type: Number,
        required: true,
        default: 0
    },
    DirVento: {
        type: Number,
        required: true,
        default: 0
    },
    VelVento: {
        type: Number,
        required: true,
        default: 0
    },
    Temperatura: {
        type: Date,
        required: true,
        default: 0
    },
    Pressao: {
        type: Number,
        required: true,
        default: 0
    },
    Umidade: {
        type: Number,
        required: true,
        default: 0
    },
    teste: {
        type: Number,
        required: false,
        default: 0
    }
})

const WeatherStation = mongoose.model('weatherStation', wsSchema)

module.exports = WeatherStation