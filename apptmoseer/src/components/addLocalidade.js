import {Link} from "react-router-dom"

function AddLocalidade() {
    return(
        <>
        <main>
        <img src={process.env.PUBLIC_URL + "/logo.png"} width="120px" height="100px"/>
        <form id="adicionarLocalidade">
            <select id="estado" name="estado">
                <option value="" disabled selected hidden>Estado</option>
                <option value="AC">Acre</option>
                <option value="AL">Alagoas</option>
                <option value="AP">Amapá</option>
                <option value="AM">Amazonas</option>
                <option value="BA">Bahia</option>
                <option value="CE">Ceará</option>
                <option value="DF">Distrito Federal</option>
                <option value="ES">Espírito Santo</option>
                <option value="GO">Goiás</option>
                <option value="MA">Maranhão</option>
                <option value="MT">Mato Grosso</option>
                <option value="MS">Mato Grosso do Sul</option>
                <option value="MG">Minas Gerais</option>
                <option value="PA">Pará</option>
                <option value="PB">Paraíba</option>
                <option value="PR">Paraná</option>
                <option value="PE">Pernambuco</option>
                <option value="PI">Piauí</option>
                <option value="RJ">Rio de Janeiro</option>
                <option value="RN">Rio Grande do Norte</option>
                <option value="RS">Rio Grande do Sul</option>
                <option value="RO">Rondônia</option>
                <option value="RR">Roraima</option>
                <option value="SC">Santa Catarina</option>
                <option value="SP">São Paulo</option>
                <option value="SE">Sergipe</option>
                <option value="TO">Tocantins</option>
            </select>
            <input type="text" id="cidade" name="cidade" placeholder="Cidade"/>
            <input type="submit" value="Buscar" id="buscarLocalidade" />
        </form>
        </main>
        <footer class="footer">
            <Link to="/localidades">x</Link>
        </footer></>
    )   
}

export default AddLocalidade