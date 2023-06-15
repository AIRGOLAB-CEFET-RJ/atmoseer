const mongoose = require('mongoose')
const Schema = mongoose.Schema

const soundingSchema = new Schema ({
    pressure: {
        type: Number,
        required: true,
        default: 0
    },
    height: {
        type: Number,
        required: true,
        default: 0
    },
    temperature: {
        type: Number,
        required: true,
        default: 0
    },
    dewpoint: {
        type: Number,
        required: true,
        default: 0
    },
    direction: {
        type: Number,
        required: true,
        default: 0
    },
    speed: {
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

const Sounding = mongoose.model('Sounding', soundingSchema)

module.exports = Sounding