//   Importando Express: um framework para Node.js voltado para o desenvolvimento web, servindo como uma camada de abstração 
// para simplificar a criação de aplicativos e APIs web
const express = require('express')
//   Importando Mongoose: uma biblioteca do Node.js que trabalha com o MongoDB, um banco de dados do NoSQL, criando uma 
// camada de abstração que facilita na interação com os documentos do banco de dados
const mongoose = require('mongoose')

//Definição da URL de conexão com o MongoDB
const mongoURI = 'mongodb://127.0.0.1:27017/db' //'mongodb://localhost/db'

// Initializando Express.js
const app = express()

// Configuração de porta 3000 e exibição de mensagem no console como confirmação
app.listen(3000, () => {
   console.log('Listening for request on port 3000');
});

// Importando os dados das quatro fontes: Sondas, COR, InMet e Era5
const soundingRouter = require('./routes/Sounding')
const corRouter = require('./routes/COR')
const inmetRouter = require('./routes/Inmet')
//const era5Router = require('./routes/Era5')

// Definição das rotas de cada fonte
app.use('/sounding', soundingRouter)
app.use('/cor', corRouter)
app.use('/inmet', inmetRouter)
//app.use('/era5', era5Router)

// Inicialização e armazenamento da conexão no URL definido
mongoose.connect(mongoURI)
db = mongoose.connection
db.on('error', console.error.bind(console, 'connection error:'))

// Exportando para o objeto app
module.exports = app