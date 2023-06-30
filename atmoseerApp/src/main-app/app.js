import React, { useEffect } from 'react'
import {
    BrowserRouter as Router,
    Routes,
    Route
} from "react-router-dom"

import Header from '../components/header.js'
import Home from '../components/home.js'
import Localidade from '../components/localidade.js'
import AddLocalidade from '../components/addLocalidade.js'

const App = () => {
    return(
        <Router>
            <Header />
            <Routes>
                <Route exact path="/" element={<Home />} />
                <Route exact path="/localidades" element={<Localidade />} />
                <Route exact path="/addLocalidade" element={<AddLocalidade />} />
            </Routes>
        </Router>
    )
}

export default App