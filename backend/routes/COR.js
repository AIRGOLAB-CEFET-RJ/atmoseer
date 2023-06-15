var express = require('express')
var router = express.Router()
const COR = require('../dbmodels/COR.js')

var weatherData = []

function getRandomNumber(min, max) {
    return Math.random() * (max - min) + min;
}

function WeatherData() {
    const stations = ['Vidigal', 'Irajá', 'Jardim Botânico', 'Barra/Riocentro', 'Guaratiba', 'Santa Cruz', 'Alto da Boa Vista', 'São Cristóvão']
    const data = new Date()
    weatherData = []

    stations.forEach(station => {
        const quantidade_chuva = getRandomNumber(0, 10).toFixed(2) // Quantidade de chuva em milímetros
        const umidade_relativa = getRandomNumber(10, 90).toFixed(2) // Umidade relativa do ar
        const temperatura_media = getRandomNumber(20, 40).toFixed(2) // Temperatura média em °C
        const direcao_vento = Math.floor(getRandomNumber(0, 360)) // Direção do vento em graus
        const velocidade_vento = getRandomNumber(20, 100).toFixed(2) // Velocidade do vento em km/h
        const pressao_atmosferica = getRandomNumber(900, 1100).toFixed(2) // Pressão atmosférica em hPa

        const stationData = {
            data: data,
            nome: station,
            quantidade_chuva: quantidade_chuva,
            umidade_relativa: umidade_relativa,
            temperatura_media: temperatura_media,
            direcao_vento: direcao_vento,
            velocidade_vento: velocidade_vento,
            pressao_atmosferica: pressao_atmosferica
        };
    
        weatherData.push(stationData);
    })

    COR.insertMany(weatherData)
    .then(() => {
        console.log('Dados meteorológicos salvos no MongoDB com sucesso.')
    })
    .catch((error) => {
        console.error('Erro ao salvar dados meteorológicos no MongoDB:', error)
    })
}

setInterval(WeatherData, 15 * 60 * 1000)
WeatherData()

router.get('/', (request, response) => {
    response.json(weatherData)
})

module.exports = router;