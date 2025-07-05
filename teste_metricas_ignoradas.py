import pandas as pd
import logging
from conversor import ExcelToSQLiteConverter
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def testar_metricas_ignoradas():
    """Testa se as métricas específicas estão sendo ignoradas corretamente"""
    excel_file = "data/Planilha Mensal 2025.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        return
    
    print("🔍 TESTANDO IGNORAÇÃO DE MÉTRICAS ESPECÍFICAS...")
    print("="*80)
    
    # Ler Excel
    try:
        df = pd.read_excel(excel_file, sheet_name=0, header=None)
        print(f"✅ Excel carregado: {len(df)} linhas, {len(df.columns)} colunas")
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return
    
    # Métricas que devem ser ignoradas
    metricas_ignorar = [
        'múltiplas ameaças relacionadas à abrangência do tráfico',
        'multiplas ameacas relacionadas a abrangencia do trafico',
        'múltiplas ameaças',
        'multiplas ameacas'
    ]
    
    print(f"\n📋 PROCURANDO MÉTRICAS A IGNORAR:")
    
    # Procurar por todas as métricas no Excel
    todas_metricas = []
    for idx, row in df.iterrows():
        if pd.notna(row.iloc[0]) and isinstance(row.iloc[0], str):
            metric_name = str(row.iloc[0]).strip()
            if metric_name:
                todas_metricas.append({
                    'linha': idx,
                    'nome': metric_name,
                    'nome_lower': metric_name.lower()
                })
    
    print(f"   Total de métricas encontradas no Excel: {len(todas_metricas)}")
    
    # Verificar métricas que devem ser ignoradas
    print(f"\n🚫 MÉTRICAS QUE DEVEM SER IGNORADAS:")
    metricas_encontradas = []
    for metrica_ignorar in metricas_ignorar:
        encontrada = False
        for metrica in todas_metricas:
            if metrica_ignorar.lower() in metrica['nome_lower'] or metrica['nome_lower'] in metrica_ignorar.lower():
                print(f"   ✅ '{metrica_ignorar}' encontrada na linha {metrica['linha']}: '{metrica['nome']}'")
                metricas_encontradas.append(metrica)
                encontrada = True
                break
        if not encontrada:
            print(f"   ⚠️  '{metrica_ignorar}' NÃO encontrada")
    
    # Testar o processamento completo
    print(f"\n🔧 TESTANDO PROCESSAMENTO COMPLETO:")
    sqlite_test_file = "teste_metricas_ignoradas.db"
    
    # Remover arquivo de teste se existir
    if os.path.exists(sqlite_test_file):
        os.remove(sqlite_test_file)
    
    with ExcelToSQLiteConverter(excel_file, sqlite_test_file) as converter:
        success = converter.process_excel()
        
        if success:
            print(f"   ✅ Processamento concluído com sucesso")
            
            # Verificar se as métricas foram ignoradas no banco
            import sqlite3
            conn = sqlite3.connect(sqlite_test_file)
            
            # Buscar pelas métricas que deveriam ser ignoradas
            for metrica_ignorar in metricas_ignorar:
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM dados_mensais 
                    WHERE LOWER(metrica) LIKE ?
                ''', (f'%{metrica_ignorar}%',))
                
                count = cursor.fetchone()[0]
                if count == 0:
                    print(f"   ✅ '{metrica_ignorar}' foi corretamente ignorada (0 registros)")
                else:
                    print(f"   ❌ '{metrica_ignorar}' NÃO foi ignorada ({count} registros encontrados)")
            
            # Mostrar estatísticas gerais
            cursor = conn.execute("SELECT COUNT(*) FROM dados_mensais")
            total_registros = cursor.fetchone()[0]
            print(f"\n   📊 Total de registros no banco: {total_registros}")
            
            # Mostrar algumas métricas processadas (exemplo)
            cursor = conn.execute('''
                SELECT DISTINCT metrica FROM dados_mensais 
                ORDER BY metrica 
                LIMIT 10
            ''')
            metricas_processadas = cursor.fetchall()
            
            print(f"\n   📋 Exemplos de métricas processadas:")
            for metrica in metricas_processadas:
                print(f"     - {metrica[0]}")
            
            conn.close()
        else:
            print(f"   ❌ Falha no processamento")
    
    # Limpar arquivo de teste
    if os.path.exists(sqlite_test_file):
        os.remove(sqlite_test_file)
        print(f"\n   🗑️  Arquivo de teste removido")
    
    print(f"\n" + "="*80)
    print("TESTE CONCLUÍDO!")

if __name__ == "__main__":
    testar_metricas_ignoradas() 