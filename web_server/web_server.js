const express = require('express');
const app = express();
const login = require('../authentication/details.json');

app.set('view engine', 'ejs');
app.set('views', __dirname + '/views');
app.use(express.urlencoded({extended: true}));
app.use(express.json());

const fs = require("fs");

const { Client } = require('pg');
const client = new Client(login);
client.connect();

const port = 3000;


console.log(login);

app.get('/', async function (req, res) {
    console.log(req.body);
    res.render('index', {
        timestamps: await getTimestamps(),
        databases: await getDatabases(),
        image: undefined,
        imageTimestamp: undefined
    });
});

app.post('/', async function (req, res) {
    res.render('index', {
        timestamps: await getTimestamps(),
        databases: await getDatabases(),
        image: await getImage(req.body.dropdownTimestamp),
        imageTimestamp: req.body.dropdownTimestamp
    });
})

app.listen(port, "0.0.0.0", function () {
        console.log('Listening on port 3000');
});


// Return last 25 timestamps
async function getTimestamps() {
    let data;
    await client.query('SELECT timestamp FROM images ORDER BY timestamp DESC LIMIT 25').then(res => {
        data = res.rows.map(element => {
            return element.timestamp.toLocaleString();
        });
    })
    return data;
}

// Return all connected databases
async function getDatabases(){
    let data;
    await client.query('SELECT datname from pg_database').then(res => {
        data = res.rows.map(element => {
            return element.datname;
        });
    })
    return data;
}

// Return image at timestamp
async function getImage(ts){
    let value = [ts]
    let data;
    await client.query("SELECT encode(data, 'escape') FROM images WHERE timestamp=$1", value).then(res => {
        data = res.rows.map(element => {
            return element;
        });
    })
    var source = 'data:image/jpeg;base64,' + data[0].encode;
    return source;
}