import {Link} from "react-router-dom"

function Home() {
    return(
        <>
        <main>
            <img src={process.env.PUBLIC_URL + "/logo.png"} width="240px" height="200px" />
        </main>
        <footer class="footer">
            <Link to="/localidades">+</Link>
        </footer></>
    )   
}

export default Home;