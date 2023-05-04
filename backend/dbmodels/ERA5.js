const mongoose = require('mongoose')
const Schema = mongoose.Schema

//const normalize = require('normalize-mongoose');

const era5Schema = new Schema ({
    geopotential: {
        type: Number,
        required: true,
        default: 0
    },
    relative_humidity: {
        type: Number,
        required: true,
        default: 0
    },
    temperature: {
        type: Number,
        required: true,
        default: 0
    },
    u_component_of_wind: {
        type: Number,
        required: true,
        default: 0
    },
    v_component_of_wind: {
        type: Number,
        required: true,
        default: 0
    },
    pressure_level: {
        type: Number,
        required: true,
        default: 0
    },
    year: {
        type: Number,
        required: true,
        default: 0
    },
    month: {
        type: Number,
        required: true,
        default: 0
    },
    day: {
        type: Number,
        required: true,
        default: 0
    },
    time: {
        type: Date,
        required: true,
        default: 0
    }
})

//ERA5.plugin(normalize);

const ERA5 = mongoose.model('ERA5', era5Schema)

module.exports = ERA5