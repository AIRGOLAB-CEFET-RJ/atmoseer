const mongoose = require('mongoose')
const Schema = mongoose.Schema

const corSchema = new Schema ({
    data: { type: Date, required: true },
    nome: { type: String, required: true },
    quantidade_chuva: { type: Number, required: true },
    umidade_relativa: { type: Number, required: true },
    temperatura_media: { type: Number, required: true },
    direcao_vento: { type: Number, required: true },
    velocidade_vento: { type: Number, required: true },
    pressao_atmosferica: { type: Number, required: true }
})

const COR = mongoose.model('COR', corSchema)

module.exports = COR