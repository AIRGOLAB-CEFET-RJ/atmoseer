const mongoose = require('mongoose')
const Schema = mongoose.Schema

//    SCHEMA DO ERA5... Não utilizado no momento pois esse modelo é enviado manualmente
// para o banco de dados.

//const normalize = require('normalize-mongoose');

const era5Schema = new Schema ({
    time: {
        type: Date,
        required: true,
        default: 0
    },
    Geopotential_200: {
        type: Number,
        required: true,
        default: 0
    },
    Humidity_200: {
        type: Number,
        required: true,
        default: 0
    },
    Temperature_200: {
        type: Number,
        required: true,
        default: 0
    },
    WindU_200: {
        type: Number,
        required: true,
        default: 0
    },
    WindV_200: {
        type: Number,
        required: true,
        default: 0
    },
    Geopotential_700: {
        type: Number,
        required: true,
        default: 0
    },
    Humidity_700: {
        type: Number,
        required: true,
        default: 0
    },
    Temperature_700: {
        type: Number,
        required: true,
        default: 0
    },
    WindU_700: {
        type: Number,
        required: true,
        default: 0
    },
    WindV_700: {
        type: Number,
        required: true,
        default: 0
    },
    Geopotential_1000: {
        type: Number,
        required: true,
        default: 0
    },
    Humidity_1000: {
        type: Number,
        required: true,
        default: 0
    },
    Temperature_1000: {
        type: Number,
        required: true,
        default: 0
    },
    WindU_1000: {
        type: Number,
        required: true,
        default: 0
    },
    WindV_1000: {
        type: Number,
        required: true,
        default: 0
    }
})

//ERA5.plugin(normalize);

const ERA5 = mongoose.model('ERA5', era5Schema)

module.exports = ERA5