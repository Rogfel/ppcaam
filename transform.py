import glob
import json
import pandas as pd


def step_1():
    '''
    Consolida arquivos Excel de diferentes estados em um único arquivo CSV.
    Cada arquivo Excel deve estar nomeado no formato "dados_estado.xlsx", onde "estado" é a sigla do estado (AL, AC, BA, AM, AP).
    1. Lê todos os arquivos Excel na pasta "origen".
    2. Adiciona uma coluna "estado" com a sigla do estado correspondente.
    3. Concatena todos os dados em um único DataFrame.
    4. Salva o DataFrame consolidado em um arquivo CSV chamado "dados_consolidados_PPCAAM.csv".
    5. Imprime o número total de linhas consolidadas.
    '''
    # Lista todos os arquivos Excel na pasta atual
    arquivos_excel = glob.glob("origen/*.xlsx")

    # Lista para armazenar todos os DataFrames
    todos_dados = []

    # Lê cada arquivo e adiciona à lista
    for arquivo in arquivos_excel:
        # Extrai o estado do nome do arquivo (AL, AC, BA, AM, AP)
        estado = arquivo.split('_')[-1].split('.')[0]
        
        # Lê o arquivo Excel
        df = pd.read_excel(arquivo)
        
        # Adiciona uma coluna com o estado
        df['estado'] = estado
        
        # Adiciona à lista
        todos_dados.append(df)

    # Concatena todos os DataFrames
    dados_consolidados = pd.concat(todos_dados, ignore_index=True)

    # Salva como CSV
    dados_consolidados.to_csv("dados_consolidados_PPCAAM.csv", index=False, encoding='utf-8-sig')

    print(f"Arquivos consolidados com sucesso! Total de linhas: {len(dados_consolidados)}")

def step_2():
    '''
    Letura de arquivo CSV consolidado e exibição de amostra dos dados.
    Elimina as filas com primeira coluna igual a CONTROLE ou vazia.
    1. Lê o arquivo CSV "dados_consolidados_PPCAAM.csv".
    2. Exibe as primeiras linhas do DataFrame.
    3. Exibe informações do DataFrame.
    4. Exibe a contagem de linhas e colunas.
    5. Elimina as filas com primeira coluna igual a CONTROLE ou vazia.
    6. Exibe a contagem de linhas e colunas após a limpeza.
    7. Salva o DataFrame limpo em "dados_limpos_PPCAAM.csv".
    8. Imprime mensagem de sucesso.
    '''
    # Lê o arquivo CSV consolidado
    dados = pd.read_csv("dados_consolidados_PPCAAM.csv", encoding='utf-8-sig')
    print(f"\nContagem de linhas e colunas antes da limpeza: {dados.shape}")
    # Elimina filas com primeira coluna igual a CONTROLE ou vazia
    primeira_coluna = dados.columns[0]
    dados_limpos = dados[(dados[primeira_coluna] != 'CONTROLE') & (dados[primeira_coluna].notna())]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Programa de Proteção a Crianças e Adolescentes Ameaçados de Morte (PPCAAM)')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Ficha de Coleta de Dados Quantitativos dos Programas Estaduais')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Identificação') & (dados_limpos[primeira_coluna] != 'Ano Referência')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Unidade do PPCAAM') & (dados_limpos[primeira_coluna] != 'Responsável pelo preenchimento ')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Coleta mensal') & (dados_limpos[primeira_coluna] != 'Criança/Adolescente incluído ')]
    print(f"\nContagem de linhas e colunas após a limpeza: {dados_limpos.shape}")
    # Salva o DataFrame limpo
    dados_limpos.to_csv("dados_limpos_PPCAAM.csv", index=False, encoding='utf-8-sig')
    print("Dados limpos salvos com sucesso em 'dados_limpos_PPCAAM.csv'.")

def step_2_5():
    '''
    Letura de arquivo CSV limpo e exibição de amostra dos dados.
    1. Lê o arquivo CSV "dados_limpos_PPCAAM.csv".
    2. Exibe as primeiras linhas do DataFrame.
    3. Exibe informações do DataFrame.
    4. Exibe a contagem de linhas e colunas.
    '''
    # Lê o arquivo CSV limpo
    dados = pd.read_csv("dados_limpos_PPCAAM.csv", encoding='utf-8-sig')
    primeira_coluna = dados.columns[0]
    dados_limpos = dados[(dados[primeira_coluna] != 'Educação de Jovens e Adultos')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Especifique quais (Outros):')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Múltiplas Ameaças relacionadas à Abrangência do Tráfico')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Especifique quais:')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Múltiplas Ameaças')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Registra-se que as pessoas desligadas no mês de novembro estão em acompanhamento de pós-desligamento.')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Comentários Adicionais')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != '''O estado teve 1 caso de ameaças múltiplas: [1] Violência Sexual: Abuso Sexual e Violência domestica.                                                                                                                                                                                                                                                                                                          													
														
														
														''')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != 'Para o caso de pessoas que estão cursando o EJA, favor marcar a série completa correspondente e registrar no campo abaixo o quantitativo de pessoas incluídas no mês que estão cursando o EJA.')]
    dados_limpos = dados_limpos[(dados_limpos[primeira_coluna] != '''1 (um) protegidos com histórico de EJA														
														
														''')]
    print(f"\nContagem de linhas e colunas após a limpeza: {dados_limpos.shape}")
    # Salva o DataFrame limpo
    dados_limpos.to_csv("dados_limpos2_PPCAAM.csv", index=False, encoding='utf-8-sig')
    print("Dados limpos v2 salvos com sucesso em 'dados_limpos2_PPCAAM.csv'.")

def step_3(ano_referencia):
    '''
    Transformar o dataframe para as colunas de:
    [ano_referencia, secao, metrica, ano_anterior, janeiro, fevereiro, marco, abril, maio,
     junho, julho, agosto, setembro, outubro, novembro, dezembro, unidade]
    '''
    # Lê o arquivo CSV limpo
    dados = pd.read_csv("dados_limpos2_PPCAAM.csv", encoding='utf-8-sig')
    # Define um dataframe vazio para os dados transformados
    dados_transformados = pd.DataFrame(columns=['ano_referencia', 'unidade', 'secao', 'metrica', 'ano_anterior',
                                              'janeiro', 'fevereiro', 'marco', 'abril', 'maio',
                                              'junho', 'julho', 'agosto', 'setembro', 'outubro',
                                              'novembro', 'dezembro'])
    # letura do json de mapeamento
    secao_map = json.load(open('secao.json', 'r', encoding='utf-8'))
    secao_list = secao_map['secao']
    
    secao = ''
    # Itera sobre as linhas do dataframe original e transforma os dados
    for index, row in dados.iterrows():
        # Extrai os dados necessários e adiciona ao novo dataframe
        if row['Unnamed: 0'] in secao_list:
            secao = row['Unnamed: 0']
            continue
        unidade = row['estado']
        metrica = row['Unnamed: 0']
        ano_anterior = row['Ministério dos Direitos Humanos e da Cidadania']
        meses = { 'janeiro': row['Unnamed: 2'], 'fevereiro': row['Unnamed: 3'], 'marco': row['Unnamed: 4'],
                   'abril': row['Unnamed: 5'], 'maio': row['Unnamed: 6'], 'junho': row['Unnamed: 7'],
                   'julho': row['Unnamed: 8'], 'agosto': row['Unnamed: 9'], 'setembro': row['Unnamed: 10'],
                   'outubro': row['Unnamed: 11'], 'novembro': row['Unnamed: 12'], 'dezembro': row['Unnamed: 13'] }
        nova_linha = {
            'ano_referencia': ano_referencia,
            'unidade': unidade,
            'secao': secao,
            'metrica': metrica,
            'ano_anterior': ano_anterior,
            **meses,
            'total': row['Unnamed: 14']
        }
        dados_transformados = pd.concat(
            [dados_transformados, pd.DataFrame([nova_linha])], 
            ignore_index=True
        )
    # Salva o dataframe transformado
    dados_transformados.to_csv("dados_transformados_PPCAAM.csv", index=False, encoding='utf-8-sig')
    


if __name__ == "__main__":
    step_1()
    step_2()
    step_2_5()
    step_3(ano_referencia=2025)