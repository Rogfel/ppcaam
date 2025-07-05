import pandas as pd
import sqlite3
import openpyxl
from datetime import datetime
import re
import logging
import os
import glob

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelToSQLiteConverter:
    def __init__(self, excel_path, sqlite_path):
        self.excel_path = excel_path
        self.sqlite_path = sqlite_path
        self.conn = sqlite3.connect(sqlite_path)
        self.meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
        
        # Métricas que devem ser ignoradas (não inserir no banco)
        self.metricas_ignorar = [
            'múltiplas ameaças relacionadas à abrangência do tráfico',
            'multiplas ameacas relacionadas a abrangencia do trafico',
            'múltiplas ameaças',
            'multiplas ameacas',
            'total',
            'subtotal',
            'soma',
            'soma total'
        ]
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
    
    def clean_column_name(self, name):
        """Limpa nomes de colunas para uso em SQL"""
        if pd.isna(name) or name is None:
            return "unnamed"
        # Remove caracteres especiais e substitui espaços por underscore
        clean_name = re.sub(r'[^\w\s]', '', str(name))
        clean_name = re.sub(r'\s+', '_', clean_name.strip())
        # Garantir que não seja vazio
        if not clean_name:
            return "unnamed"
        return clean_name.lower()
    
    def extract_identification_data(self, df):
        """Extrai dados de identificação da planilha"""
        identification_data = {}
        
        # Buscar dados de identificação nas primeiras linhas
        for idx, row in df.iterrows():
            if idx > 30:  # Aumentar limite de busca
                break
                
            first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            
            if "Ano Referência" in first_col or "Ano de Referência" in first_col:
                identification_data['ano_referencia'] = row.iloc[2] if len(row) > 2 else None
            elif "Unidade do PPCAAM" in first_col or "Unidade" in first_col:
                identification_data['unidade'] = row.iloc[2] if len(row) > 2 else None
            elif "Responsável pelo preenchimento" in first_col or "Responsável" in first_col:
                identification_data['responsavel'] = row.iloc[2] if len(row) > 2 else None
        
        return identification_data
    
    def find_data_sections(self, df):
        """Encontra as seções de dados na planilha - versão melhorada"""
        sections = {}
        current_section = None
        data_started = False
        section_start_row = None
        
        # Seções que devem ser ignoradas (não contêm dados tabulares)
        secoes_ignorar = [
            'comentários adicionais', 'comentarios adicionais', 'observações', 'observacoes',
            'notas', 'informações gerais', 'informacoes gerais', 'cabeçalho', 'cabecalho'
        ]
        
        # Palavras-chave expandidas para capturar mais seções
        keywords = [
            'informações', 'desligamentos', 'solicitações', 'perfil', 'por ', 'motivo', 'tempo', 
            'crianças', 'adolescentes', 'pessoas', 'protegidas', 'atendimentos', 'casos',
            'medidas', 'proteção', 'acolhimento', 'família', 'comunidade', 'deficiência', 'deficiencia',
            'violência', 'violencia', 'sexual', 'desligamento', 'retornou', 'local', 'risco',
            'vítima', 'vitima', 'deficiência', 'deficiencia', 'pessoa com deficiência',
            'pessoa com deficiencia', 'no ato do desligamento', 'ato do desligamento'
        ]
        
        for idx, row in df.iterrows():
            # Verificar se é uma linha de título de seção
            non_empty_cells = [x for x in row if pd.notna(x) and str(x).strip()]
            
            if len(non_empty_cells) == 1 and pd.notna(row.iloc[0]):
                section_name = str(row.iloc[0]).strip()
                section_name_lower = section_name.lower()
                
                # Verificar se deve ignorar esta seção
                if any(ignorar in section_name_lower for ignorar in secoes_ignorar):
                    logger.info(f"Seção ignorada: {section_name}")
                    continue
                
                # Verificar se é uma seção de dados (usando palavras-chave ou seções específicas)
                is_data_section = any(keyword in section_name_lower for keyword in keywords)
                
                # Verificar seções específicas mencionadas pelo usuário
                secoes_especificas = [
                    'pessoa com deficiência', 'pessoa com deficiencia',
                    'vítima de violência sexual', 'vitima de violencia sexual',
                    'no ato do desligamento, a pessoa protegida retornou ao local de risco?',
                    'no ato do desligamento, a pessoa protegida retornou ao local de risco'
                ]
                
                if any(especifica in section_name_lower for especifica in secoes_especificas):
                    is_data_section = True
                
                if is_data_section:
                    # Finalizar seção anterior se existir
                    if current_section and section_start_row is not None:
                        sections[current_section] = list(range(section_start_row, idx))
                        logger.info(f"Seção finalizada: {current_section} (linhas {section_start_row}-{idx-1})")
                    
                    current_section = section_name
                    section_start_row = idx
                    data_started = False
                    logger.info(f"Nova seção encontrada: {current_section} (linha {idx})")
            
            # Verificar se é uma linha de dados (tem mais de 2 células preenchidas)
            elif current_section and len(non_empty_cells) > 2:
                # Verificar se contém meses ou números (indica início dos dados)
                row_str = ' '.join([str(x) for x in row if pd.notna(x)]).lower()
                if any(mes in row_str for mes in self.meses) or any(str(x).isdigit() for x in row[1:] if pd.notna(x)):
                    data_started = True
                
                if data_started and section_start_row is not None:
                    # Adicionar linha à seção atual
                    if current_section not in sections:
                        sections[current_section] = []
                    sections[current_section].append(idx)
        
        # Finalizar última seção
        if current_section and section_start_row is not None:
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].extend(list(range(section_start_row, len(df))))
            logger.info(f"Última seção finalizada: {current_section}")
        
        return sections
    
    def process_monthly_data(self, df, section_rows, section_name):
        """Processa dados mensais de uma seção - versão melhorada"""
        if not section_rows:
            return []
        
        # Encontrar linha de cabeçalho (que contém os meses)
        header_row = None
        for row_idx in section_rows:
            row = df.iloc[row_idx]
            row_str = ' '.join([str(x) for x in row if pd.notna(x)]).lower()
            if any(mes in row_str for mes in self.meses):
                header_row = row_idx
                break
        
        if header_row is None:
            logger.warning(f"Não foi encontrado cabeçalho com meses na seção: {section_name}")
            # Tentar processar sem cabeçalho de meses (para seções com formato diferente)
            return self.process_section_without_monthly_header(df, section_rows, section_name)
        
        # Extrair cabeçalhos
        headers = []
        header_data = df.iloc[header_row]
        for col in header_data:
            if pd.notna(col):
                headers.append(self.clean_column_name(str(col)))
        
        logger.info(f"Cabeçalhos encontrados na seção {section_name}: {headers}")
        
        # Processar linhas de dados
        processed_data = []
        for row_idx in section_rows:
            if row_idx <= header_row:  # Pular cabeçalho
                continue
                
            row = df.iloc[row_idx]
            if pd.notna(row.iloc[0]) and isinstance(row.iloc[0], str):
                # Esta é uma linha de dados com descrição
                metric_name = str(row.iloc[0]).strip()
                
                # Verificar se a métrica deve ser ignorada
                metric_name_lower = metric_name.lower()
                if any(ignorar in metric_name_lower for ignorar in self.metricas_ignorar):
                    logger.info(f"Métrica ignorada: {metric_name}")
                    continue
                
                # Pular linhas vazias ou que não são métricas
                if not metric_name:
                    continue
                
                # Extrair valores mensais
                row_data = {
                    'secao': section_name,
                    'metrica': metric_name,
                    'ano': None
                }
                
                # Mapear valores para os meses
                for i, value in enumerate(row[1:], 1):
                    if i < len(headers):
                        col_name = headers[i]
                        if col_name in ['2024', '2025', '2023']:
                            row_data['ano'] = int(col_name)
                        elif col_name in self.meses:
                            # Converter para número, tratar valores vazios
                            if pd.notna(value) and value != "":
                                try:
                                    row_data[col_name] = float(value) if isinstance(value, (int, float)) else 0
                                except (ValueError, TypeError):
                                    row_data[col_name] = 0
                            else:
                                row_data[col_name] = 0
                        elif col_name in ['total', 'total_anual']:
                            if pd.notna(value) and value != "":
                                try:
                                    row_data['total_anual'] = float(value) if isinstance(value, (int, float)) else 0
                                except (ValueError, TypeError):
                                    row_data['total_anual'] = 0
                            else:
                                row_data['total_anual'] = 0
                
                # Calcular total anual se não foi fornecido
                if row_data.get('total_anual') is None or row_data['total_anual'] == 0:
                    total = sum(row_data.get(mes, 0) for mes in self.meses)
                    row_data['total_anual'] = total
                
                processed_data.append(row_data)
        
        logger.info(f"Processados {len(processed_data)} registros na seção {section_name}")
        return processed_data
    
    def process_section_without_monthly_header(self, df, section_rows, section_name):
        """Processa seções que não têm cabeçalho mensal tradicional"""
        logger.info(f"Processando seção sem cabeçalho mensal: {section_name}")
        
        processed_data = []
        
        for row_idx in section_rows:
            row = df.iloc[row_idx]
            
            # Verificar se é uma linha com dados
            non_empty_cells = [x for x in row if pd.notna(x) and str(x).strip()]
            
            if len(non_empty_cells) >= 2 and pd.notna(row.iloc[0]):
                metric_name = str(row.iloc[0]).strip()
                
                # Verificar se a métrica deve ser ignorada
                metric_name_lower = metric_name.lower()
                if any(ignorar in metric_name_lower for ignorar in self.metricas_ignorar):
                    logger.info(f"Métrica ignorada (sem cabeçalho): {metric_name}")
                    continue
                
                # Pular linhas vazias ou que não são métricas
                if not metric_name:
                    continue
                
                # Para seções sem cabeçalho mensal, tentar extrair valores numéricos
                row_data = {
                    'secao': section_name,
                    'metrica': metric_name,
                    'ano': None
                }
                
                # Procurar por valores numéricos nas colunas
                valores_encontrados = 0
                for i, value in enumerate(row[1:], 1):
                    if pd.notna(value) and value != "":
                        try:
                            valor_numerico = float(value) if isinstance(value, (int, float)) else 0
                            if valor_numerico > 0:
                                # Mapear para meses baseado na posição (se possível)
                                if i <= 12:
                                    mes_idx = i - 1
                                    if mes_idx < len(self.meses):
                                        row_data[self.meses[mes_idx]] = valor_numerico
                                        valores_encontrados += 1
                                else:
                                    # Se não couber nos meses, adicionar como total
                                    row_data['total_anual'] = valor_numerico
                        except (ValueError, TypeError):
                            pass
                
                # Se encontrou valores, adicionar ao resultado
                if valores_encontrados > 0:
                    # Calcular total se não foi fornecido
                    if row_data.get('total_anual') is None:
                        total = sum(row_data.get(mes, 0) for mes in self.meses)
                        row_data['total_anual'] = total
                    
                    processed_data.append(row_data)
        
        logger.info(f"Processados {len(processed_data)} registros na seção {section_name} (sem cabeçalho mensal)")
        return processed_data
    
    def create_tables(self):
        """Cria as tabelas no SQLite"""
        
        # Tabela de identificação
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS identificacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano_referencia INTEGER,
                unidade TEXT,
                responsavel TEXT,
                data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela principal de dados mensais
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS dados_mensais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                secao TEXT NOT NULL,
                metrica TEXT NOT NULL,
                ano INTEGER,
                jan REAL DEFAULT 0,
                fev REAL DEFAULT 0,
                mar REAL DEFAULT 0,
                abr REAL DEFAULT 0,
                mai REAL DEFAULT 0,
                jun REAL DEFAULT 0,
                jul REAL DEFAULT 0,
                ago REAL DEFAULT 0,
                set_mes REAL DEFAULT 0,
                out_mes REAL DEFAULT 0,
                nov REAL DEFAULT 0,
                dez REAL DEFAULT 0,
                total_anual REAL DEFAULT 0,
                data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(secao, metrica, ano)
            )
        ''')
        
        # Tabela de log de importações
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS log_importacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arquivo_origem TEXT,
                total_registros INTEGER,
                data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.info("Tabelas criadas com sucesso")
    
    def insert_or_update_data(self, data_list, ano):
        """Insere novos dados ou soma aos existentes - versão melhorada"""
        updated_count = 0
        inserted_count = 0
        
        for data in data_list:
            if not data.get('secao') or not data.get('metrica'):
                continue
            
            # Verificar se registro já existe
            cursor = self.conn.execute('''
                SELECT id, jan, fev, mar, abr, mai, jun, jul, ago, set_mes, out_mes, nov, dez, total_anual
                FROM dados_mensais 
                WHERE secao = ? AND metrica = ? AND ano = ?
            ''', (data['secao'], data['metrica'], ano))
            
            existing = cursor.fetchone()
            
            if existing:
                # Somar aos valores existentes
                existing_id = existing[0]
                new_values = {}
                for i, mes in enumerate(['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set_mes', 'out_mes', 'nov', 'dez'], 1):
                    existing_val = existing[i] or 0
                    new_val = data.get(mes.replace('_mes', ''), 0) or 0
                    new_values[mes] = existing_val + new_val
                
                # Calcular novo total
                existing_total = existing[13] or 0
                new_total = data.get('total_anual', 0) or 0
                new_values['total_anual'] = existing_total + new_total
                
                # Atualizar registro
                self.conn.execute('''
                    UPDATE dados_mensais 
                    SET jan = ?, fev = ?, mar = ?, abr = ?, mai = ?, jun = ?, jul = ?, ago = ?, 
                        set_mes = ?, out_mes = ?, nov = ?, dez = ?, total_anual = ?,
                        data_importacao = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    new_values['jan'], new_values['fev'], new_values['mar'], new_values['abr'],
                    new_values['mai'], new_values['jun'], new_values['jul'], new_values['ago'],
                    new_values['set_mes'], new_values['out_mes'], new_values['nov'], new_values['dez'],
                    new_values['total_anual'], existing_id
                ))
                updated_count += 1
                
            else:
                # Inserir novo registro
                self.conn.execute('''
                    INSERT INTO dados_mensais 
                    (secao, metrica, ano, jan, fev, mar, abr, mai, jun, jul, ago, set_mes, out_mes, nov, dez, total_anual)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['secao'], data['metrica'], ano,
                    data.get('jan', 0), data.get('fev', 0), data.get('mar', 0), data.get('abr', 0),
                    data.get('mai', 0), data.get('jun', 0), data.get('jul', 0), data.get('ago', 0),
                    data.get('set', 0), data.get('out', 0), data.get('nov', 0), data.get('dez', 0),
                    data.get('total_anual', 0)
                ))
                inserted_count += 1
        
        self.conn.commit()
        logger.info(f"Dados processados: {inserted_count} inseridos, {updated_count} atualizados")
        return inserted_count, updated_count
    
    def process_excel(self):
        """Processa o arquivo Excel completo - versão melhorada"""
        logger.info(f"Iniciando processamento do arquivo: {self.excel_path}")
        
        # Ler arquivo Excel
        try:
            df = pd.read_excel(self.excel_path, sheet_name=0, header=None)
            logger.info(f"Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo Excel: {e}")
            return False
        
        # Criar tabelas
        self.create_tables()
        
        # Extrair dados de identificação
        identification = self.extract_identification_data(df)
        if identification:
            self.conn.execute('''
                INSERT INTO identificacao (ano_referencia, unidade, responsavel)
                VALUES (?, ?, ?)
            ''', (identification.get('ano_referencia'), identification.get('unidade'), identification.get('responsavel')))
            self.conn.commit()
            logger.info(f"Dados de identificação inseridos: {identification}")
        
        # Encontrar seções de dados
        sections = self.find_data_sections(df)
        logger.info(f"Encontradas {len(sections)} seções de dados")
        
        # Processar cada seção
        all_data = []
        for section_name, section_rows in sections.items():
            if section_rows:
                logger.info(f"Processando seção: {section_name} ({len(section_rows)} linhas)")
                section_data = self.process_monthly_data(df, section_rows, section_name)
                all_data.extend(section_data)
                logger.info(f"Seção '{section_name}': {len(section_data)} registros processados")
        
        # Inserir/atualizar dados
        if all_data:
            ano = identification.get('ano_referencia') if identification else 2025
            inserted, updated = self.insert_or_update_data(all_data, ano)
            
            # Log da importação
            self.conn.execute('''
                INSERT INTO log_importacoes (arquivo_origem, total_registros)
                VALUES (?, ?)
            ''', (self.excel_path, len(all_data)))
            self.conn.commit()
            
            logger.info(f"Processamento concluído: {len(all_data)} registros totais")
            return True
        else:
            logger.warning("Nenhum dado foi encontrado para processar")
            return False
    
    def get_summary(self):
        """Retorna um resumo dos dados no banco"""
        cursor = self.conn.execute('''
            SELECT secao, COUNT(*) as total_metricas, 
                   SUM(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total_valores
            FROM dados_mensais 
            GROUP BY secao
            ORDER BY secao
        ''')
        
        results = cursor.fetchall()
        return results

def process_all_excel_files(data_folder="data", sqlite_file="ppcaam_dados.db"):
    """Processa todos os arquivos Excel (.xlsx) na pasta data"""
    logger.info(f"Procurando arquivos Excel na pasta: {data_folder}")
    
    # Verificar se a pasta existe
    if not os.path.exists(data_folder):
        logger.error(f"Pasta {data_folder} não encontrada")
        return False
    
    # Encontrar todos os arquivos .xlsx
    excel_files = glob.glob(os.path.join(data_folder, "*.xlsx"))
    
    if not excel_files:
        logger.warning(f"Nenhum arquivo .xlsx encontrado na pasta {data_folder}")
        return False
    
    logger.info(f"Encontrados {len(excel_files)} arquivos Excel: {[os.path.basename(f) for f in excel_files]}")
    
    # Processar cada arquivo
    success_count = 0
    total_files = len(excel_files)
    
    for i, excel_file in enumerate(excel_files, 1):
        logger.info(f"Processando arquivo {i}/{total_files}: {os.path.basename(excel_file)}")
        
        try:
            # Criar novo converter para cada arquivo
            with ExcelToSQLiteConverter(excel_file, sqlite_file) as file_converter:
                success = file_converter.process_excel()
                if success:
                    success_count += 1
                    logger.info(f"✅ Arquivo {os.path.basename(excel_file)} processado com sucesso")
                else:
                    logger.warning(f"⚠️ Arquivo {os.path.basename(excel_file)} não foi processado completamente")
                    
        except Exception as e:
            logger.error(f"❌ Erro ao processar {os.path.basename(excel_file)}: {e}")
            continue
    
    logger.info(f"Processamento concluído: {success_count}/{total_files} arquivos processados com sucesso")
    return success_count > 0

def main():
    """Função principal para executar a conversão"""
    excel_file = "data/Planilha Mensal 2025.xlsx"  # Altere para o caminho do seu arquivo
    sqlite_file = "ppcaam_dados.db"  # Nome do arquivo SQLite de destino
    
    # Verificar se existe apenas um arquivo específico ou processar todos
    if os.path.exists(excel_file):
        # Processar arquivo específico
        try:
            with ExcelToSQLiteConverter(excel_file, sqlite_file) as converter:
                success = converter.process_excel()
                
                if success:
                    print(f"\n✅ Conversão concluída com sucesso!")
                    print(f"Arquivo processado: {excel_file}")
                    print(f"Banco de dados SQLite: {sqlite_file}")
                    
                    # Mostrar resumo
                    summary = converter.get_summary()
                    print(f"\n📊 Resumo dos dados:")
                    print(f"{'Seção':<50} {'Métricas':<10} {'Total Valores':<15}")
                    print("-" * 75)
                    for secao, total_metricas, total_valores in summary:
                        print(f"{secao[:47]:<50} {total_metricas:<10} {total_valores or 0:<15.0f}")
                        
                else:
                    print("❌ Erro durante a conversão. Verifique os logs.")
                    
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            print(f"❌ Erro: {e}")
    else:
        # Processar todos os arquivos Excel na pasta data
        print("📁 Processando todos os arquivos Excel na pasta 'data'...")
        success = process_all_excel_files("data", sqlite_file)
        
        if success:
            print(f"\n✅ Processamento de múltiplos arquivos concluído!")
            print(f"Banco de dados SQLite: {sqlite_file}")
            
            # Mostrar resumo final
            try:
                with ExcelToSQLiteConverter("", sqlite_file) as converter:
                    summary = converter.get_summary()
                    print(f"\n📊 Resumo final dos dados consolidados:")
                    print(f"{'Seção':<50} {'Métricas':<10} {'Total Valores':<15}")
                    print("-" * 75)
                    for secao, total_metricas, total_valores in summary:
                        print(f"{secao[:47]:<50} {total_metricas:<10} {total_valores or 0:<15.0f}")
            except Exception as e:
                print(f"Erro ao mostrar resumo: {e}")
        else:
            print("❌ Erro durante o processamento dos arquivos. Verifique os logs.")

def consultar_dados(sqlite_file="ppcaam_dados.db"):
    """Função para consultar e validar os dados no SQLite"""
    conn = sqlite3.connect(sqlite_file)
    
    print("=" * 80)
    print("CONSULTA DE DADOS NO BANCO SQLITE")
    print("=" * 80)
    
    # 1. Informações de identificação
    cursor = conn.execute("SELECT * FROM identificacao ORDER BY data_importacao DESC LIMIT 1")
    ident = cursor.fetchone()
    if ident:
        print(f"\n📋 IDENTIFICAÇÃO:")
        print(f"   Ano de Referência: {ident[1]}")
        print(f"   Unidade: {ident[2]}")
        print(f"   Responsável: {ident[3]}")
        print(f"   Data de Importação: {ident[4]}")
    
    # 2. Log de importações
    cursor = conn.execute("SELECT * FROM log_importacoes ORDER BY data_importacao DESC")
    logs = cursor.fetchall()
    print(f"\n📁 HISTÓRICO DE IMPORTAÇÕES:")
    for log in logs:
        print(f"   {log[3]}: {log[1]} ({log[2]} registros)")
    
    # 3. Resumo por seção
    cursor = conn.execute('''
        SELECT secao, COUNT(*) as metricas, 
               AVG(total_anual) as media_anual,
               SUM(total_anual) as soma_total
        FROM dados_mensais 
        GROUP BY secao 
        ORDER BY soma_total DESC
    ''')
    print(f"\n📊 RESUMO POR SEÇÃO:")
    print(f"{'Seção':<45} {'Métricas':<8} {'Média Anual':<12} {'Total':<10}")
    print("-" * 80)
    for row in cursor.fetchall():
        secao = row[0][:42] + "..." if len(row[0]) > 45 else row[0]
        print(f"{secao:<45} {row[1]:<8} {row[2]:<12.1f} {row[3]:<10.0f}")
    
    # 4. Dados mensais de uma seção específica (exemplo)
    cursor = conn.execute('''
        SELECT metrica, jan, fev, mar, abr, mai, jun, jul, ago, set_mes, out_mes, nov, dez, total_anual
        FROM dados_mensais 
        WHERE secao = "Informações sobre Pessoas Protegidas"
        ORDER BY metrica
    ''')
    dados_exemplo = cursor.fetchall()
    if dados_exemplo:
        print(f"\n📈 EXEMPLO - Informações sobre Pessoas Protegidas:")
        print(f"{'Métrica':<40} {'Jan':<4} {'Fev':<4} {'Mar':<4} {'Total':<6}")
        print("-" * 65)
        for row in dados_exemplo:
            metrica = row[0][:37] + "..." if len(row[0]) > 40 else row[0]
            print(f"{metrica:<40} {row[1]:<4.0f} {row[2]:<4.0f} {row[3]:<4.0f} {row[13]:<6.0f}")
    
    # 5. Verificar dados consolidados
    cursor = conn.execute('''
        SELECT COUNT(*) as total_registros,
               COUNT(DISTINCT secao) as total_secoes,
               COUNT(DISTINCT metrica) as total_metricas,
               SUM(jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total_geral
        FROM dados_mensais
    ''')
    stats = cursor.fetchone()
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   Total de registros: {stats[0]}")
    print(f"   Total de seções: {stats[1]}")
    print(f"   Total de métricas únicas: {stats[2]}")
    print(f"   Soma total de todos os valores: {stats[3]:.0f}")
    
    conn.close()
    print("\n" + "=" * 80)

def executar_consulta_personalizada(sqlite_file="ppcaam_dados.db", query=None):
    """Executa uma consulta SQL personalizada"""
    if not query:
        query = input("Digite sua consulta SQL: ")
    
    conn = sqlite3.connect(sqlite_file)
    try:
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        # Mostrar nomes das colunas
        col_names = [description[0] for description in cursor.description]
        print(f"\n{'  |  '.join(col_names)}")
        print("-" * (len('  |  '.join(col_names))))
        
        # Mostrar resultados
        for row in results:
            print(f"{'  |  '.join([str(x) if x is not None else 'NULL' for x in row])}")
            
    except sqlite3.Error as e:
        print(f"Erro na consulta: {e}")
    finally:
        conn.close()

def exemplo_uso_consolidacao():
    """Demonstra como funciona a consolidação de dados"""
    print("\n" + "=" * 80)
    print("EXEMPLO DE COMO FUNCIONA A CONSOLIDAÇÃO")
    print("=" * 80)
    print("""
Este script realiza as seguintes operações:

1. 📂 LEITURA DO EXCEL:
   - Identifica automaticamente as seções de dados
   - Extrai informações de identificação (ano, unidade, responsável)
   - Processa dados mensais de cada seção

2. 🗄️ CRIAÇÃO DO BANCO SQLITE:
   - Tabela 'identificacao': dados gerais da planilha
   - Tabela 'dados_mensais': valores mensais por seção e métrica
   - Tabela 'log_importacoes': histórico de importações

3. 🔄 CONSOLIDAÇÃO INTELIGENTE:
   - Se um registro já existe (mesma seção, métrica e ano): SOMA os valores
   - Se é um registro novo: INSERE normalmente
   - Mantém histórico de todas as importações

4. 📊 EXEMPLO DE CONSOLIDAÇÃO:
   Execução 1: 'Nº total de crianças protegidas' em Jan = 10
   Execução 2: 'Nº total de crianças protegidas' em Jan = 5
   Resultado final: Jan = 15 (10 + 5)

5. 🔍 CONSULTAS DISPONÍVEIS:
   - Resumo por seções
   - Dados mensais detalhados
   - Histórico de importações
   - Consultas SQL personalizadas
""")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--consultar":
            consultar_dados()
        elif sys.argv[1] == "--exemplo":
            exemplo_uso_consolidacao()
        elif sys.argv[1] == "--query":
            if len(sys.argv) > 2:
                executar_consulta_personalizada(query=sys.argv[2])
            else:
                executar_consulta_personalizada()
        elif sys.argv[1] == "--todos":
            # Processar todos os arquivos Excel na pasta data
            print("📁 Processando todos os arquivos Excel na pasta 'data'...")
            success = process_all_excel_files("data", "ppcaam_dados.db")
            
            if success:
                print(f"\n✅ Processamento de múltiplos arquivos concluído!")
                print(f"Banco de dados SQLite: ppcaam_dados.db")
                
                # Mostrar resumo final
                try:
                    with ExcelToSQLiteConverter("", "ppcaam_dados.db") as converter:
                        summary = converter.get_summary()
                        print(f"\n📊 Resumo final dos dados consolidados:")
                        print(f"{'Seção':<50} {'Métricas':<10} {'Total Valores':<15}")
                        print("-" * 75)
                        for secao, total_metricas, total_valores in summary:
                            print(f"{secao[:47]:<50} {total_metricas:<10} {total_valores or 0:<15.0f}")
                except Exception as e:
                    print(f"Erro ao mostrar resumo: {e}")
            else:
                print("❌ Erro durante o processamento dos arquivos. Verifique os logs.")
        else:
            print("Opções disponíveis:")
            print("  python conversor.py              # Executar conversão (arquivo específico ou todos)")
            print("  python conversor.py --todos      # Processar todos os arquivos Excel na pasta data")
            print("  python conversor.py --consultar  # Consultar dados")
            print("  python conversor.py --exemplo    # Ver exemplo de uso")
            print("  python conversor.py --query      # Executar consulta SQL")
    else:
        main()
