import pandas as pd
import logging
from conversor import ExcelToSQLiteConverter
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def testar_secoes_especificas():
    """Testa se as seções específicas mencionadas pelo usuário estão sendo capturadas"""
    excel_file = "data/Planilha Mensal 2025.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        return
    
    print("🔍 TESTANDO CAPTURA DE SEÇÕES ESPECÍFICAS...")
    print("="*80)
    
    # Ler Excel
    try:
        df = pd.read_excel(excel_file, sheet_name=0, header=None)
        print(f"✅ Excel carregado: {len(df)} linhas, {len(df.columns)} colunas")
    except Exception as e:
        print(f"❌ Erro ao carregar Excel: {e}")
        return
    
    # Seções específicas que devem ser encontradas
    secoes_esperadas = [
        'pessoa com deficiência',
        'vítima de violência sexual', 
        'no ato do desligamento, a pessoa protegida retornou ao local de risco?'
    ]
    
    # Seções que devem ser ignoradas
    secoes_ignorar = [
        'comentários adicionais'
    ]
    
    print(f"\n📋 PROCURANDO SEÇÕES ESPECÍFICAS:")
    
    # Procurar por todas as seções no Excel
    todas_secoes = []
    for idx, row in df.iterrows():
        non_empty_cells = [x for x in row if pd.notna(x) and str(x).strip()]
        if len(non_empty_cells) == 1 and pd.notna(row.iloc[0]):
            section_name = str(row.iloc[0]).strip()
            todas_secoes.append({
                'linha': idx,
                'nome': section_name,
                'nome_lower': section_name.lower()
            })
    
    print(f"   Total de seções encontradas no Excel: {len(todas_secoes)}")
    
    # Verificar seções esperadas
    print(f"\n✅ SEÇÕES ESPERADAS:")
    secoes_encontradas = []
    for secao_esperada in secoes_esperadas:
        encontrada = False
        for secao in todas_secoes:
            if secao_esperada.lower() in secao['nome_lower'] or secao['nome_lower'] in secao_esperada.lower():
                print(f"   ✅ '{secao_esperada}' encontrada na linha {secao['linha']}: '{secao['nome']}'")
                secoes_encontradas.append(secao)
                encontrada = True
                break
        if not encontrada:
            print(f"   ❌ '{secao_esperada}' NÃO encontrada")
    
    # Verificar seções a ignorar
    print(f"\n🚫 SEÇÕES A IGNORAR:")
    for secao_ignorar in secoes_ignorar:
        encontrada = False
        for secao in todas_secoes:
            if secao_ignorar.lower() in secao['nome_lower']:
                print(f"   ✅ '{secao_ignorar}' encontrada na linha {secao['linha']}: '{secao['nome']}' (será ignorada)")
                encontrada = True
                break
        if not encontrada:
            print(f"   ⚠️  '{secao_ignorar}' NÃO encontrada")
    
    # Testar o algoritmo de detecção
    print(f"\n🔧 TESTANDO ALGORITMO DE DETECÇÃO:")
    with ExcelToSQLiteConverter(excel_file, "teste_secoes.db") as converter:
        sections = converter.find_data_sections(df)
        
        print(f"   Seções detectadas pelo algoritmo: {len(sections)}")
        for secao_nome, secao_linhas in sections.items():
            print(f"     - '{secao_nome}' ({len(secao_linhas)} linhas)")
    
    # Verificar se as seções esperadas foram detectadas
    print(f"\n📊 RESULTADO DA DETECÇÃO:")
    secoes_detectadas = list(sections.keys())
    secoes_detectadas_lower = [s.lower() for s in secoes_detectadas]
    
    for secao_esperada in secoes_esperadas:
        detectada = any(secao_esperada.lower() in detectada or detectada in secao_esperada.lower() 
                       for detectada in secoes_detectadas_lower)
        if detectada:
            print(f"   ✅ '{secao_esperada}' foi detectada pelo algoritmo")
        else:
            print(f"   ❌ '{secao_esperada}' NÃO foi detectada pelo algoritmo")
    
    # Mostrar todas as seções encontradas
    print(f"\n📋 TODAS AS SEÇÕES ENCONTRADAS NO EXCEL:")
    for i, secao in enumerate(todas_secoes, 1):
        status = ""
        if any(esperada.lower() in secao['nome_lower'] for esperada in secoes_esperadas):
            status = " (ESPERADA)"
        elif any(ignorar.lower() in secao['nome_lower'] for ignorar in secoes_ignorar):
            status = " (IGNORAR)"
        elif any(secao['nome_lower'] in detectada for detectada in secoes_detectadas_lower):
            status = " (DETECTADA)"
        
        print(f"   {i:2d}. Linha {secao['linha']:3d}: '{secao['nome']}'{status}")
    
    print(f"\n" + "="*80)
    print("TESTE CONCLUÍDO!")

if __name__ == "__main__":
    testar_secoes_especificas() 