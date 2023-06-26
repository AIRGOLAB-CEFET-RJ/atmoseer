var express = require('express')
var router = express.Router()

//Importando o schema do mongodb do COR
const COR = require('../dbmodels/COR.js')

var weatherData = []

//Função getRandomNumber: Gera um número aleatório em um intervalo
function getRandomNumber(min, max) {
    return Math.random() * (max - min) + min;
}

//Função WeatherData: Gera os dados do COR e os armazena no mongodb
function WeatherData() {
    //Estações meteorológicas do COR
    const stations = ['Vidigal', 'Irajá', 'Jardim Botânico', 'Barra/Riocentro', 'Guaratiba', 'Santa Cruz', 'Alto da Boa Vista', 'São Cristóvão']
    
    //Pega a data atual
    const data = new Date()

    weatherData = []

    stations.forEach(station => {
        const precipitation = getRandomNumber(0, 10).toFixed(2) // Quantidade de chuva em milímetros
        const wind_dir = Math.floor(getRandomNumber(0, 360)) // Direção do vento em graus
        const wind_speed = getRandomNumber(20, 100).toFixed(2) // Velocidade do vento em km/h
        const temperature = getRandomNumber(20, 40).toFixed(2) // Temperatura média em °C
        const pressure = getRandomNumber(900, 1100).toFixed(2) // Pressão atmosférica em hPa
        const humidity = getRandomNumber(10, 90).toFixed(2) // Umidade relativa do ar

        //Armazena os dados gerados em um objeto COR
        const stationData = new COR( {
            precipitation: precipitation,
            wind_dir: wind_dir,
            wind_speed: wind_speed,
            temperature: temperature,
            pressure: pressure,
            humidity: humidity,
            station: station,
            datetime: data
        })
    
        weatherData.push(stationData);
    })

    //Salva os dados no mongodb
    COR.insertMany(weatherData)
    .then(() => {
        console.log('Dados meteorológicos salvos no MongoDB com sucesso.')
    })
    .catch((error) => {
        console.error('Erro ao salvar dados meteorológicos no MongoDB:', error)
    })
}

//A função WeatherData será executada a cada 15 minutos
setInterval(WeatherData, 15 * 60 * 1000)
WeatherData()

router.get('/', (request, response) => {
    response.json(weatherData)
})

module.exports = router;