# Surface Stations - Estações de Superfície

Módulo para recuperação de dados de estações meteorológicas e hidrológicas.

## 📊 Fontes de Dados

### 1. ANA - Agência Nacional de Águas

Script: `retrieve_ws_ana.py`

**Dados disponíveis:**
- 💧 Precipitação (chuva)
- 🌊 Vazão de rios
- 📅 Dados históricos desde 1930

**Autenticação:** ✅ Requerida (OAuth)

**Scripts disponíveis:**
- `retrieve_ws_ana.py` - Baixar dados
- `analisar_dados_ana.py` - Analisar dados baixados

**Como usar:**
```bash
# Configure o ambiente
$env:PYTHONPATH = "src"

# 1. Baixar dados
python src\surface_stations\retrieve_ws_ana.py `
  -u SEU_CPF `
  -p SUA_SENHA `
  -s 2141006 `
  -b 2020 `
  -e 2024

# 2. Analisar dados baixados
python src\surface_stations\analisar_dados_ana.py 2141006
```

**Ajuda:**
```bash
python src\surface_stations\retrieve_ws_ana.py -h
python src\surface_stations\analisar_dados_ana.py
```

---

## 🔐 Credenciais

Para obter credenciais da API da ANA:

1. Envie e-mail para: **hidro@ana.gov.br**
2. Assunto: `[SEU_CPF] - Solicitação de acesso à API HidroWebService`
3. Aguarde aprovação (3-7 dias úteis)

---

## 🗺️ Estações Configuradas

Estações da região do Rio de Janeiro (configuradas em `src/config/globals.py`):

| Código | Localização | Tipo |
|--------|-------------|------|
| 2141006 | DOIS RIOS - São Fidélis | Pluviométrica |
| 2141007 | TRÊS IRMÃOS - Cambuci | Pluviométrica |
| 2141043 | SÃO FIDELIS | Pluviométrica |
| 2141078 | ITALVA PREFEITURA | Pluviométrica |
| 2242004 | RIO DE JANEIRO - SANTA CRUZ | Pluviométrica |
| 2242008 | RIO DE JANEIRO - GRANDE HOTEL | Pluviométrica |
| 2242015 | RIO DE JANEIRO - JARDIM BOTÂNICO | Pluviométrica |
| 2242016 | RIO DE JANEIRO - GRAJAÚ | Pluviométrica |

---

## 📦 Formato de Saída

Os dados são salvos em formato **Parquet** em `data/ws/ana/`:

```
data/
└── ws/
    └── ana/
        ├── 2141006.parquet
        ├── 2141007.parquet
        └── ...
```

**Vantagens do Parquet:**
- ✅ Compressão eficiente
- ✅ Leitura rápida
- ✅ Preservação de tipos de dados
- ✅ Compatível com Pandas, Spark, Dask

**Como ler:**
```python
import pandas as pd

df = pd.read_parquet('data/ws/ana/2141006.parquet')
print(df.head())
```

---

## 🔗 Links Úteis

- **Portal HidroWeb:** https://www.snirh.gov.br/hidroweb/
- **API Swagger:** https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html#/
- **Site da ANA:** https://www.gov.br/ana/

---

## 📝 Exemplos de Uso

### Exemplo 1: Download Básico

```bash
python src\surface_stations\retrieve_ws_ana.py `
  -u 12345678900 `
  -p "minhasenha" `
  -s 2141006 `
  -b 2020 `
  -e 2024
```

### Exemplo 2: Apenas Chuva

```bash
python src\surface_stations\retrieve_ws_ana.py `
  -u 12345678900 `
  -p "minhasenha" `
  -s 2141006 `
  -b 2020 `
  -e 2024 `
  -t 2
```

### Exemplo 3: Todas as Estações

```bash
python src\surface_stations\retrieve_ws_ana.py `
  -u 12345678900 `
  -p "minhasenha" `
  -s all `
  -b 2020 `
  -e 2024
```

### Exemplo 4: Análise em Python

```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar dados
df = pd.read_parquet('data/ws/ana/2141006.parquet')

# Converter data
df['Data'] = pd.to_datetime(df['Data'])

# Análise mensal
df.set_index('Data', inplace=True)
mensal = df['Chuva'].resample('M').sum()

# Plotar
plt.figure(figsize=(12, 6))
plt.plot(mensal.index, mensal.values)
plt.title('Precipitação Mensal')
plt.xlabel('Mês')
plt.ylabel('Precipitação (mm)')
plt.grid(True)
plt.show()
```

---

## 🛠️ Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'config'"

**Solução:**
```bash
$env:PYTHONPATH = "src"
```

### Erro: "Erro na autenticação (HTTP 401)"

**Solução:**
- Verifique se o CPF está sem pontos ou traços
- Confirme que a senha está correta
- Coloque a senha entre aspas

### Erro: "Nenhum dado retornado"

**Solução:**
- Verifique se a estação tem dados para o período
- Consulte o Portal HidroWeb
- Tente outro período


