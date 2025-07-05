# exemplo_uso.py
"""
Script de exemplo mostrando como usar o conversor Excel para SQLite
e demonstrando a funcionalidade de consolidação de dados
"""

import sqlite3
import os
from datetime import datetime

def demonstracao_completa():
    """Demonstração completa do funcionamento do sistema"""
    
    print("🚀 DEMONSTRAÇÃO DO CONVERSOR EXCEL PARA SQLITE")
    print("=" * 60)
    
    # Verificar se o arquivo Excel existe
    excel_file = "data/Planilha Mensal 2025.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo {excel_file} não encontrado!")
        print("   Certifique-se de que o arquivo está no mesmo diretório.")
        return
    
    # Importar o conversor
    try:
        from conversor import ExcelToSQLiteConverter
    except ImportError:
        print("❌ Módulo conversor não encontrado!")
        print("   Certifique-se de ter o arquivo conversor.py")
        return
    
    sqlite_file = "teste_ppcaam.db"
    
    # Primeira execução - dados iniciais
    print("\n📥 PRIMEIRA EXECUÇÃO - Importando dados iniciais...")
    with ExcelToSQLiteConverter(excel_file, sqlite_file) as converter:
        success = converter.process_excel()
        if success:
            print("✅ Primeira importação concluída!")
            resumo1 = converter.get_summary()
        else:
            print("❌ Erro na primeira importação")
            return
    
    # Simular segunda execução (dados adicionais)
    print("\n📥 SEGUNDA EXECUÇÃO - Simulando consolidação...")
    simular_segunda_importacao(sqlite_file)
    
    # Mostrar resultados
    print("\n📊 RESULTADO FINAL APÓS CONSOLIDAÇÃO:")
    mostrar_comparacao(sqlite_file)
    
    print(f"\n✅ Demonstração concluída!")
    print(f"   Banco de dados salvo como: {sqlite_file}")
    print(f"   Use: python conversor.py.py --consultar")

def simular_segunda_importacao(sqlite_file):
    """Simula uma segunda importação para demonstrar a consolidação"""
    conn = sqlite3.connect(sqlite_file)
    
    # Buscar alguns registros existentes para modificar
    cursor = conn.execute('''
        SELECT secao, metrica, ano, jan, fev, mar 
        FROM dados_mensais 
        WHERE jan > 0 OR fev > 0 OR mar > 0
        LIMIT 3
    ''')
    
    registros = cursor.fetchall()
    
    print("   Adicionando valores aos registros existentes...")
    for registro in registros:
        secao, metrica, ano, jan_atual, fev_atual, mar_atual = registro
        
        # Simular novos valores para somar
        novos_valores = {
            'jan': 2,
            'fev': 3,
            'mar': 1
        }
        
        # Atualizar com soma (simulando o comportamento do conversor)
        conn.execute('''
            UPDATE dados_mensais 
            SET jan = jan + ?, fev = fev + ?, mar = mar + ?
            WHERE secao = ? AND metrica = ? AND ano = ?
        ''', (novos_valores['jan'], novos_valores['fev'], novos_valores['mar'],
              secao, metrica, ano))
        
        print(f"   ✓ {metrica[:40]}... (Jan: {jan_atual}+{novos_valores['jan']}={jan_atual+novos_valores['jan']})")
    
    # Adicionar log da "segunda importação"
    conn.execute('''
        INSERT INTO log_importacoes (arquivo_origem, total_registros)
        VALUES (?, ?)
    ''', ("Simulação de segunda importação", len(registros)))
    
    conn.commit()
    conn.close()

def mostrar_comparacao(sqlite_file):
    """Mostra uma comparação dos dados antes e depois da consolidação"""
    conn = sqlite3.connect(sqlite_file)
    
    # Mostrar log de importações
    cursor = conn.execute("SELECT * FROM log_importacoes ORDER BY data_importacao")
    logs = cursor.fetchall()
    
    print("\n📋 Histórico de Importações:")
    for i, log in enumerate(logs, 1):
        print(f"   {i}. {log[1]} - {log[2]} registros ({log[3]})")
    
    # Mostrar alguns dados consolidados
    cursor = conn.execute('''
        SELECT secao, metrica, jan, fev, mar, total_anual
        FROM dados_mensais 
        WHERE jan > 0 OR fev > 0 OR mar > 0
        ORDER BY secao, metrica
        LIMIT 5
    ''')
    
    print(f"\n📊 Exemplos de Dados Consolidados:")
    print(f"{'Seção':<25} {'Métrica':<30} {'Jan':<4} {'Fev':<4} {'Mar':<4}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        secao = row[0][:22] + "..." if len(row[0]) > 25 else row[0]
        metrica = row[1][:27] + "..." if len(row[1]) > 30 else row[1]
        print(f"{secao:<25} {metrica:<30} {row[2]:<4.0f} {row[3]:<4.0f} {row[4]:<4.0f}")
    
    conn.close()

def validar_estrutura_banco(sqlite_file="ppcaam_dados.db"):
    """Valida a estrutura do banco de dados"""
    
    if not os.path.exists(sqlite_file):
        print(f"❌ Banco de dados {sqlite_file} não encontrado!")
        return False
    
    conn = sqlite3.connect(sqlite_file)
    
    print(f"\n🔍 VALIDAÇÃO DA ESTRUTURA DO BANCO: {sqlite_file}")
    print("-" * 50)
    
    # Verificar tabelas
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [row[0] for row in cursor.fetchall()]
    
    tabelas_esperadas = ['identificacao', 'dados_mensais', 'log_importacoes']
    
    print("📋 Tabelas encontradas:")
    for tabela in tabelas:
        status = "✅" if tabela in tabelas_esperadas else "⚠️"
        print(f"   {status} {tabela}")
    
    # Verificar colunas da tabela principal
    cursor = conn.execute("PRAGMA table_info(dados_mensais)")
    colunas = cursor.fetchall()
    
    print(f"\n📊 Estrutura da tabela 'dados_mensais':")
    for col in colunas:
        print(f"   {col[1]} ({col[2]})")
    
    # Contadores
    cursor = conn.execute("SELECT COUNT(*) FROM dados_mensais")
    total_registros = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(DISTINCT secao) FROM dados_mensais")
    total_secoes = cursor.fetchone()[0]
    
    print(f"\n📈 Estatísticas:")
    print(f"   Total de registros: {total_registros}")
    print(f"   Total de seções: {total_secoes}")
    
    conn.close()
    return True

def gerar_relatorio_completo(sqlite_file="ppcaam_dados.db"):
    """Gera um relatório completo dos dados"""
    
    if not validar_estrutura_banco(sqlite_file):
        return
    
    conn = sqlite3.connect(sqlite_file)
    
    print(f"\n📄 RELATÓRIO COMPLETO DOS DADOS")
    print("=" * 50)
    
    # 1. Informações gerais
    cursor = conn.execute("SELECT * FROM identificacao ORDER BY data_importacao DESC LIMIT 1")
    ident = cursor.fetchone()
    if ident:
        print(f"\n🏢 Informações da Unidade:")
        print(f"   Ano: {ident[1]}")
        print(f"   Unidade: {ident[2]}")
        print(f"   Responsável: {ident[3]}")
    
    # 2. Resumo por seção com totais
    cursor = conn.execute('''
        SELECT 
            secao,
            COUNT(*) as total_metricas,
            SUM(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total_anual,
            AVG(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as media_por_metrica
        FROM dados_mensais 
        GROUP BY secao 
        ORDER BY total_anual DESC
    ''')
    
    print(f"\n📊 Resumo por Seção:")
    print(f"{'Seção':<40} {'Métricas':<8} {'Total':<8} {'Média':<8}")
    print("-" * 70)
    
    total_geral = 0
    for row in cursor.fetchall():
        secao = row[0][:37] + "..." if len(row[0]) > 40 else row[0]
        total_anual = row[2] or 0
        media = row[3] or 0
        total_geral += total_anual
        print(f"{secao:<40} {row[1]:<8} {total_anual:<8.0f} {media:<8.1f}")
    
    print("-" * 70)
    print(f"{'TOTAL GERAL':<40} {'':<8} {total_geral:<8.0f}")
    
    # 3. Top 10 métricas com maiores valores
    cursor = conn.execute('''
        SELECT 
            metrica,
            secao,
            (jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total
        FROM dados_mensais 
        WHERE total > 0
        ORDER BY total DESC
        LIMIT 10
    ''')
    
    print(f"\n🏆 Top 10 Métricas com Maiores Valores:")
    print(f"{'Métrica':<35} {'Seção':<25} {'Total':<8}")
    print("-" * 70)
    
    for row in cursor.fetchall():
        metrica = row[0][:32] + "..." if len(row[0]) > 35 else row[0]
        secao = row[1][:22] + "..." if len(row[1]) > 25 else row[1]
        print(f"{metrica:<35} {secao:<25} {row[2]:<8.0f}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "--demo":
            demonstracao_completa()
        elif comando == "--validar":
            arquivo = sys.argv[2] if len(sys.argv) > 2 else "ppcaam_dados.db"
            validar_estrutura_banco(arquivo)
        elif comando == "--relatorio":
            arquivo = sys.argv[2] if len(sys.argv) > 2 else "ppcaam_dados.db"
            gerar_relatorio_completo(arquivo)
        else:
            print("Comandos disponíveis:")
            print("  --demo      : Demonstração completa")
            print("  --validar   : Validar estrutura do banco")
            print("  --relatorio : Gerar relatório completo")
    else:
        print("🔧 FERRAMENTA DE TESTE E VALIDAÇÃO")
        print("=" * 40)
        print("Comandos disponíveis:")
        print("  python exemplo_uso.py --demo")
        print("  python exemplo_uso.py --validar [arquivo.db]")
        print("  python exemplo_uso.py --relatorio [arquivo.db]")
        print()
        print("Para converter Excel para SQLite:")
        print("  python conversor.py.py")