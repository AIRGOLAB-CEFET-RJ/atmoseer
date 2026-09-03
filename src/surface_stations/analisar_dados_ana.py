#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para analisar dados baixados da ANA

Uso:
    python src/surface_stations/analisar_dados_ana.py <codigo_estacao>
    
Exemplo:
    python src/surface_stations/analisar_dados_ana.py 2141006
"""

import pandas as pd
import sys
import os
from pathlib import Path

def analisar_estacao(codigo_estacao):
    """Analisa dados de uma estação"""
    
    # Caminho do arquivo
    arquivo = f'data/ws/ana/{codigo_estacao}.parquet'
    
    # Verificar se existe
    if not os.path.exists(arquivo):
        print(f"\nERRO: Arquivo nao encontrado: {arquivo}")
        print(f"\nBaixe os dados primeiro:")
        print(f'python src\\surface_stations\\retrieve_ws_ana.py -u CPF -p SENHA -s {codigo_estacao} -b 2024 -e 2024')
        return
    
    # Carregar dados
    df = pd.read_parquet(arquivo)
    
    # Cabeçalho
    print("\n" + "="*70)
    print(f"ANALISE DOS DADOS DA ANA - ESTACAO {codigo_estacao}")
    print("="*70)
    
    # Informações básicas
    print(f"\nARQUIVO: {arquivo}")
    print(f"TAMANHO: {os.path.getsize(arquivo) / 1024:.1f} KB")
    print(f"\nREGISTROS: {len(df)}")
    print(f"COLUNAS: {len(df.columns)}")
    
    # Período dos dados
    if 'Data_Hora_Dado' in df.columns:
        df['Data_Hora_Dado'] = pd.to_datetime(df['Data_Hora_Dado'])
        print(f"\nPERIODO:")
        print(f"  Inicio: {df['Data_Hora_Dado'].min():%Y-%m-%d}")
        print(f"  Fim:    {df['Data_Hora_Dado'].max():%Y-%m-%d}")
        print(f"  Dias:   {(df['Data_Hora_Dado'].max() - df['Data_Hora_Dado'].min()).days}")
    
    # Estatísticas de precipitação
    if 'Total' in df.columns:
        print(f"\nPRECIPITACAO TOTAL MENSAL (mm):")
        try:
            df['Total_Num'] = pd.to_numeric(df['Total'], errors='coerce')
            print(f"  Minimo: {df['Total_Num'].min():.1f}")
            print(f"  Maximo: {df['Total_Num'].max():.1f}")
            print(f"  Media:  {df['Total_Num'].mean():.1f}")
            print(f"  Total:  {df['Total_Num'].sum():.1f}")
        except:
            print(f"  (erro ao processar)")
    
    # Máximas diárias
    if 'Maxima' in df.columns:
        print(f"\nPRECIPITACAO MAXIMA DIARIA (mm):")
        try:
            df['Maxima_Num'] = pd.to_numeric(df['Maxima'], errors='coerce')
            print(f"  Maior valor: {df['Maxima_Num'].max():.1f}")
            print(f"  Media:       {df['Maxima_Num'].mean():.1f}")
        except:
            print(f"  (erro ao processar)")
    
    # Dias com chuva
    if 'Numero_Dias_de_Chuva' in df.columns:
        print(f"\nDIAS COM CHUVA:")
        try:
            df['Dias_Chuva_Num'] = pd.to_numeric(df['Numero_Dias_de_Chuva'], errors='coerce')
            print(f"  Total:  {df['Dias_Chuva_Num'].sum():.0f} dias")
            print(f"  Media:  {df['Dias_Chuva_Num'].mean():.1f} dias/mes")
        except:
            print(f"  (erro ao processar)")
    
    # Tabela de dados
    print(f"\n{'='*70}")
    print("DADOS MENSAIS")
    print("="*70)
    
    # Selecionar colunas principais
    colunas = []
    if 'Data_Hora_Dado' in df.columns:
        colunas.append('Data_Hora_Dado')
    if 'Total' in df.columns:
        colunas.append('Total')
    if 'Maxima' in df.columns:
        colunas.append('Maxima')
    if 'Numero_Dias_de_Chuva' in df.columns:
        colunas.append('Numero_Dias_de_Chuva')
    
    if colunas:
        # Formatar data para exibição
        df_show = df[colunas].copy()
        if 'Data_Hora_Dado' in df_show.columns:
            df_show['Data_Hora_Dado'] = df_show['Data_Hora_Dado'].dt.strftime('%Y-%m')
        
        print(df_show.to_string(index=False))
    else:
        print("Colunas principais nao encontradas")
    
    print("\n" + "="*70)
    print("ANALISE CONCLUIDA!")
    print("="*70 + "\n")


def main():
    """Função principal"""
    
    if len(sys.argv) < 2:
        print("\n" + "="*70)
        print("ANALISADOR DE DADOS DA ANA")
        print("="*70)
        print("\nUso:")
        print(f"  python {sys.argv[0]} <codigo_estacao>")
        print("\nExemplo:")
        print(f"  python {sys.argv[0]} 2141006")
        print("\nEstacoes disponiveis:")
        
        # Listar arquivos na pasta
        data_dir = 'data/ws/ana'
        if os.path.exists(data_dir):
            arquivos = [f.replace('.parquet', '') for f in os.listdir(data_dir) if f.endswith('.parquet')]
            if arquivos:
                for arq in sorted(arquivos):
                    print(f"  - {arq}")
            else:
                print("  (nenhum dado baixado ainda)")
        else:
            print("  (pasta de dados nao existe)")
        
        print("\n" + "="*70 + "\n")
        return
    
    # Obter código da estação
    codigo = sys.argv[1]
    
    # Analisar
    analisar_estacao(codigo)


if __name__ == "__main__":
    main()

