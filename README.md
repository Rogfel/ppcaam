# Conversor Excel para SQLite - PPCAAM

Sistema para converter planilhas Excel do PPCAAM (Programa de Proteção a Crianças e Adolescentes Ameaçados de Morte) para banco de dados SQLite com funcionalidade de consolidação automática de dados.

## 📋 Requisitos

```txt
pandas>=1.5.0
openpyxl>=3.0.0
sqlite3 (incluído no Python)
```

Para instalar as dependências:
```bash
pip install pandas openpyxl
```

## 🚀 Como Usar

### 1. Conversão Básica

```bash
# Converter Excel para SQLite
python conversor.py
```

### 2. Consultar Dados

```bash
# Ver resumo dos dados
python python conversor.py --consultar

# Ver exemplo de uso
python python conversor.py --exemplo

# Executar consulta SQL personalizada
python python conversor.py --query "SELECT * FROM dados_mensais LIMIT 5"
```

### 3. Demonstração e Testes

```bash
# Demonstração completa
python test_conversor.py --demo

# Validar estrutura do banco
python test_conversor.py --validar

# Gerar relatório completo
python test_conversor.py --relatorio
```

## 📊 Estrutura do Banco de Dados

### Tabela: `identificacao`
- `id`: Chave primária
- `ano_referencia`: Ano dos dados
- `unidade`: Unidade do PPCAAM
- `responsavel`: Responsável pelo preenchimento
- `data_importacao`: Timestamp da importação

### Tabela: `dados_mensais`
- `id`: Chave primária
- `secao`: Nome da seção (ex: "Informações sobre Pessoas Protegidas")
- `metrica`: Nome da métrica (ex: "Nº total de crianças protegidas")
- `ano`: Ano de referência
- `jan` a `dez`: Valores mensais
- `total_anual`: Total anual
- `data_importacao`: Timestamp da importação

### Tabela: `log_importacoes`
- `id`: Chave primária
- `arquivo_origem`: Nome do arquivo Excel
- `total_registros`: Quantidade de registros importados
- `data_importacao`: Timestamp da importação

## 🔄 Funcionalidade de Consolidação

O sistema possui **consolidação automática** de dados:

- **Primeira execução**: Dados são inseridos normalmente
- **Execuções subsequentes**: 
  - Se registro já existe (mesma seção + métrica + ano): **SOMA** os valores
  - Se é registro novo: **INSERE** normalmente

### Exemplo de Consolidação:

```
Execução 1: "Nº crianças protegidas" Jan = 10
Execução 2: "Nº crianças protegidas" Jan = 5
Resultado: "Nº crianças protegidas" Jan = 15
```

## 📁 Estrutura de Arquivos

```
projeto/
├── conversor.py  # Script principal
├── test_conversor.py             # Testes e validação
├── Planilha Mensal 2025.xlsx     # Arquivo Excel de entrada
├── ppcaam_dados.db               # Banco SQLite gerado
└── README.md                     # Esta documentação
```

## 📈 Seções Processadas

O sistema identifica e processa automaticamente as seguintes seções:

- ✅ Informações sobre Pessoas Protegidas
- ✅ Desligamentos
- ✅ Solicitações e Inclusões
- ✅ Acolhimento Institucional
- ✅ Perfil por Identidade de Gênero
- ✅ Perfil por Orientação Sexual
- ✅ Perfil por Raça/Cor
- ✅ Perfil por Idade
- ✅ Perfil por Escolaridade
- ✅ Local e Motivo da Ameaça
- ✅ Modalidades de Proteção
- ✅ Dados de Desligamento
- E muitas outras...

## 🔍 Consultas Úteis

### Ver todas as seções disponíveis:
```sql
SELECT DISTINCT secao FROM dados_mensais ORDER BY secao;
```

### Dados de uma seção específica:
```sql
SELECT metrica, jan, fev, mar, total_anual 
FROM dados_mensais 
WHERE secao = 'Informações sobre Pessoas Protegidas';
```

### Totais por mês (todas as seções):
```sql
SELECT 
    SUM(jan) as janeiro,
    SUM(fev) as fevereiro,
    SUM(mar) as marco
FROM dados_mensais;
```

### Métricas com maiores valores:
```sql
SELECT secao, metrica, 
       (jan + fev + mar + abr + mai + jun + jul + ago + set_mes + out_mes + nov + dez) as total
FROM dados_mensais 
ORDER BY total DESC 
LIMIT 10;
```

## ⚠️ Observações Importantes

1. **Backup**: Sempre faça backup do banco antes de novas importações
2. **Encoding**: O sistema trata automaticamente caracteres especiais
3. **Meses especiais**: Setembro vira `set_mes` e Outubro vira `out_mes` para evitar conflitos SQL
4. **Valores vazios**: Células vazias são tratadas como 0
5. **Logs**: Todas as importações são registradas na tabela `log_importacoes`

## 🛠️ Personalização

Para adaptar para outras planilhas, modifique:

- `find_data_sections()`: Palavras-chave para identificar seções
- `process_monthly_data()`: Formato dos dados mensais
- `meses`: Lista de abreviações dos meses

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs no terminal
2. Use `--validar` para verificar a estrutura do banco
3. Teste com `--demo` para ver exemplo funcional

## 📝 Versão

Versão 1.0 - Sistema completo de conversão e consolidação de dados PPCAAM.