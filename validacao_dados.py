import pandas as pd
import sqlite3
import logging
from conversor import ExcelToSQLiteConverter
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ValidacaoDados:
    def __init__(self, excel_path, sqlite_path):
        self.excel_path = excel_path
        self.sqlite_path = sqlite_path
        self.meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
        
    def analisar_excel_original(self):
        """Analisa o arquivo Excel original para extrair todos os dados"""
        logger.info(f"Analisando arquivo Excel original: {self.excel_path}")
        
        try:
            # Ler Excel sem processamento
            df = pd.read_excel(self.excel_path, sheet_name=0, header=None)
            logger.info(f"Excel carregado: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Extrair dados brutos
            dados_excel = {
                'total_linhas': len(df),
                'total_colunas': len(df.columns),
                'celulas_nao_vazias': 0,
                'valores_numericos': 0,
                'secoes_encontradas': [],
                'dados_detalhados': []
            }
            
            # Contar células não vazias e valores numéricos
            for idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    if pd.notna(value) and str(value).strip():
                        dados_excel['celulas_nao_vazias'] += 1
                        
                        # Verificar se é valor numérico
                        try:
                            if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace(',', '').isdigit()):
                                dados_excel['valores_numericos'] += 1
                        except:
                            pass
                
                # Identificar possíveis seções (linhas com apenas uma célula preenchida)
                non_empty_cells = [x for x in row if pd.notna(x) and str(x).strip()]
                if len(non_empty_cells) == 1 and pd.notna(row.iloc[0]):
                    section_name = str(row.iloc[0]).strip()
                    dados_excel['secoes_encontradas'].append({
                        'linha': idx,
                        'nome': section_name
                    })
            
            logger.info(f"Análise do Excel concluída: {dados_excel['celulas_nao_vazias']} células não vazias, {dados_excel['valores_numericos']} valores numéricos")
            return dados_excel, df
            
        except Exception as e:
            logger.error(f"Erro ao analisar Excel: {e}")
            return None, None
    
    def analisar_sqlite_processado(self):
        """Analisa os dados processados no SQLite"""
        logger.info(f"Analisando dados no SQLite: {self.sqlite_path}")
        
        if not os.path.exists(self.sqlite_path):
            logger.error(f"Arquivo SQLite não encontrado: {self.sqlite_path}")
            return None
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            
            # Estatísticas gerais
            cursor = conn.execute("SELECT COUNT(*) FROM dados_mensais")
            total_registros = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT secao) FROM dados_mensais")
            total_secoes = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT metrica) FROM dados_mensais")
            total_metricas = cursor.fetchone()[0]
            
            # Soma de todos os valores
            cursor = conn.execute('''
                SELECT SUM(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) 
                FROM dados_mensais
            ''')
            soma_total = cursor.fetchone()[0] or 0
            
            # Dados por seção
            cursor = conn.execute('''
                SELECT secao, COUNT(*) as metricas, 
                       SUM(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total
                FROM dados_mensais 
                GROUP BY secao
                ORDER BY secao
            ''')
            secoes_sqlite = cursor.fetchall()
            
            # Log de importações
            cursor = conn.execute("SELECT * FROM log_importacoes ORDER BY data_importacao DESC")
            logs_importacao = cursor.fetchall()
            
            conn.close()
            
            dados_sqlite = {
                'total_registros': total_registros,
                'total_secoes': total_secoes,
                'total_metricas': total_metricas,
                'soma_total': soma_total,
                'secoes_processadas': secoes_sqlite,
                'logs_importacao': logs_importacao
            }
            
            logger.info(f"Análise do SQLite concluída: {total_registros} registros, {total_secoes} seções, {total_metricas} métricas")
            return dados_sqlite
            
        except Exception as e:
            logger.error(f"Erro ao analisar SQLite: {e}")
            return None
    
    def comparar_dados(self, dados_excel, dados_sqlite):
        """Compara os dados do Excel com os do SQLite"""
        logger.info("Iniciando comparação de dados...")
        
        if not dados_excel or not dados_sqlite:
            logger.error("Dados insuficientes para comparação")
            return False
        
        print("\n" + "="*80)
        print("VALIDAÇÃO DE DADOS - EXCEL vs SQLITE")
        print("="*80)
        
        # 1. Comparação geral
        print(f"\n📊 COMPARAÇÃO GERAL:")
        print(f"   Excel - Células não vazias: {dados_excel['celulas_nao_vazias']}")
        print(f"   Excel - Valores numéricos: {dados_excel['valores_numericos']}")
        print(f"   SQLite - Total registros: {dados_sqlite['total_registros']}")
        print(f"   SQLite - Total seções: {dados_sqlite['total_secoes']}")
        print(f"   SQLite - Total métricas: {dados_sqlite['total_metricas']}")
        
        # 2. Seções encontradas vs processadas
        print(f"\n📋 SEÇÕES:")
        print(f"   Excel - Seções identificadas: {len(dados_excel['secoes_encontradas'])}")
        print(f"   SQLite - Seções processadas: {dados_sqlite['total_secoes']}")
        
        # Mostrar seções do Excel
        print(f"\n   Seções no Excel:")
        for secao in dados_excel['secoes_encontradas']:
            print(f"     - Linha {secao['linha']}: {secao['nome']}")
        
        # Mostrar seções do SQLite
        print(f"\n   Seções no SQLite:")
        for secao, metricas, total in dados_sqlite['secoes_processadas']:
            print(f"     - {secao} ({metricas} métricas, total: {total:.0f})")
        
        # 3. Verificar se todas as seções foram processadas
        secoes_excel = [s['nome'].lower() for s in dados_excel['secoes_encontradas']]
        secoes_sqlite = [s[0].lower() for s in dados_sqlite['secoes_processadas']]
        
        secoes_nao_processadas = []
        for secao_excel in secoes_excel:
            if not any(secao_excel in secao_sqlite or secao_sqlite in secao_excel for secao_sqlite in secoes_sqlite):
                secoes_nao_processadas.append(secao_excel)
        
        if secoes_nao_processadas:
            print(f"\n⚠️  SEÇÕES NÃO PROCESSADAS:")
            for secao in secoes_nao_processadas:
                print(f"     - {secao}")
        else:
            print(f"\n✅ Todas as seções foram processadas")
        
        # 4. Log de importações
        print(f"\n📁 HISTÓRICO DE IMPORTAÇÕES:")
        for log in dados_sqlite['logs_importacao']:
            print(f"   {log[3]}: {log[1]} ({log[2]} registros)")
        
        # 5. Análise de qualidade
        print(f"\n🔍 ANÁLISE DE QUALIDADE:")
        
        # Verificar se há dados suficientes
        if dados_sqlite['total_registros'] == 0:
            print("   ❌ NENHUM DADO foi processado!")
            return False
        
        # Verificar se há seções processadas
        if dados_sqlite['total_secoes'] == 0:
            print("   ❌ NENHUMA SEÇÃO foi processada!")
            return False
        
        # Verificar se há valores numéricos
        if dados_sqlite['soma_total'] == 0:
            print("   ⚠️  Todos os valores numéricos são zero")
        else:
            print(f"   ✅ Total de valores: {dados_sqlite['soma_total']:.0f}")
        
        # Verificar proporção de dados processados
        if dados_excel['valores_numericos'] > 0:
            proporcao = (dados_sqlite['total_registros'] * 12) / dados_excel['valores_numericos']
            print(f"   📈 Proporção de dados processados: {proporcao:.2%}")
            
            if proporcao < 0.5:
                print("   ⚠️  Baixa proporção de dados processados - possível perda de dados")
            elif proporcao > 2.0:
                print("   ⚠️  Alta proporção de dados processados - possível duplicação")
            else:
                print("   ✅ Proporção de dados adequada")
        
        return True
    
    def validar_processamento(self):
        """Executa a validação completa"""
        logger.info("Iniciando validação completa de dados...")
        
        # 1. Analisar Excel original
        dados_excel, df_excel = self.analisar_excel_original()
        if not dados_excel:
            return False
        
        # 2. Processar Excel para SQLite (se necessário)
        if not os.path.exists(self.sqlite_path):
            logger.info("Arquivo SQLite não existe. Processando Excel...")
            with ExcelToSQLiteConverter(self.excel_path, self.sqlite_path) as converter:
                success = converter.process_excel()
                if not success:
                    logger.error("Falha no processamento do Excel")
                    return False
        
        # 3. Analisar SQLite processado
        dados_sqlite = self.analisar_sqlite_processado()
        if not dados_sqlite:
            return False
        
        # 4. Comparar dados
        return self.comparar_dados(dados_excel, dados_sqlite)

def main():
    """Função principal de validação"""
    excel_file = "data/Planilha Mensal 2025.xlsx"
    sqlite_file = "ppcaam_dados.db"
    
    if not os.path.exists(excel_file):
        print(f"❌ Arquivo Excel não encontrado: {excel_file}")
        return
    
    print("🔍 INICIANDO VALIDAÇÃO DE DADOS...")
    print(f"   Excel: {excel_file}")
    print(f"   SQLite: {sqlite_file}")
    
    validador = ValidacaoDados(excel_file, sqlite_file)
    sucesso = validador.validar_processamento()
    
    if sucesso:
        print(f"\n✅ Validação concluída com sucesso!")
    else:
        print(f"\n❌ Validação falhou!")

if __name__ == "__main__":
    main() 