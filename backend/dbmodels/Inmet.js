const mongoose = require('mongoose')
const Schema = mongoose.Schema

const inmetSchema = new Schema ({
    COD_ESTACAO: { type: String },
    VEN_DIR: { type: Number },
    CHUVA: { type: Number },
    PRE_INS: { type: Number },
    PRE_MIN: { type: Number },
    UMD_MAX: { type: Number },
    PRE_MAX: { type: Number },
    VEN_VEL: { type: Number },
    PTO_MIN: { type: Number },
    TEM_MAX: { type: Number },
    RAD_GLO: { type: Number },
    PTO_INS: { type: Number },
    VEN_RAJ: { type: Number },
    TEM_INS: { type: Number },
    UMD_INS: { type: Number },
    TEM_MIN: { type: Number },
    UMD_MIN: { type: Number },
    PTO_MAX: { type: Number },
    TIME: { type: Date }
})

const Inmet = mongoose.model('Inmet', inmetSchema)

module.exports = Inmet