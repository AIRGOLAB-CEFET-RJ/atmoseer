var express = require('express')
var router = express.Router()

const { spawn } = require('child_process')
const fs = require("fs")
const { NetCDFReader } = require("netcdfjs")

const process = spawn('python', ['python_scripts/save_ERA5.py'])

process.on('exit', function(code) {
    console.log('child process exited with code ' + code.toString())
    fs.readFile("file.nc", (err, data) => {
        if (err) {
            console.error(err);
            return;
        }
        const reader = new NetCDFReader(data);
    })
})

module.exports = router