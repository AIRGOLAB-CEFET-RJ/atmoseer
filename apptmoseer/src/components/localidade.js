import {Link} from "react-router-dom"

function Localidade() {
    return(
        <>
        <main>
        <img src={process.env.PUBLIC_URL + "/logo.png"} width="120px" height="100px"/>
        <div class="localidade-wrapper">
            <div class="localidade">
                <div class="localidade-local">
                    <p>Pq. Araruama</p> 
                    <p>S. João de Meriti</p>
                </div>
                <div class="localidade-conteudo">
                    <img src={process.env.PUBLIC_URL + "/tempo.png"}/>
                    <div class="localidade-dados">
                        <p>Max: 32°C</p>
                        <p>Min: 28°C</p>
                        <p>Chuva: 22%</p>
                        <p>Vento: 23km/h</p>
                    </div>
                </div>
                <a href="#">Ver Mais</a>
            </div>
            <div class="localidade">
                <div class="localidade-local">
                    <p>Magé</p> 
                    <p>Dq. de Caxias</p>
                </div>
                <div class="localidade-conteudo">
                    <img src={process.env.PUBLIC_URL + "/tempo.png"}/>
                    <div class="localidade-dados">
                        <p>Max: 38°C</p>
                        <p>Min: 30°C</p>
                        <p>Chuva: 20%</p>
                        <p>Vento: 32km/h</p>
                    </div>
                </div>
                <a href="#">Ver Mais</a>
            </div>
        </div>
        </main>
        <footer class="footer">
            <Link to="/addLocalidade">+</Link>
        </footer></>
    )   
}

export default Localidade;