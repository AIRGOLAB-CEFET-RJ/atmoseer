import {Link} from "react-router-dom"

function Header() {
    return(
        <header class="header-wrapper">
            <div class="header">
                <Link to="/"><h1>AtmoSEER</h1></Link>
                <div class="checkbox-container">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="toggle" />
                        <label class="checkbox" for="toggle">
                            <div class="trace"></div>
                            <div class="trace"></div>
                            <div class="trace"></div>
                        </label>
                        <div class="menu"></div>
                        <nav class="menu-items">
                            <ul>
                                <li>
                                    <Link to="/">Home</Link>
                                </li>
                                <li>
                                    <Link to="/localidades">Localidades</Link>
                                </li>
                                <li>
                                    <Link to="/addLocalidade">Adicionar Localidade</Link>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            </div>
        </header>
    )
}

export default Header