# Automação de abertura de chamados com Selenium

Automação em Python para preencher e enviar chamados em uma aplicação web de atendimento usando Selenium e dados de um arquivo CSV.

> **Nota:** este repositório foi preparado para demonstração/portfólio. URLs, caminhos locais e informações específicas do ambiente original foram removidos. Antes de usar em um ambiente real, valide as regras de segurança e as políticas da organização responsável pelo sistema.

## O que o projeto faz

- Lê chamados a partir de um CSV;
- valida as colunas obrigatórias;
- abre o navegador com Selenium;
- permite que o usuário faça o login manualmente;
- navega até o formulário de atendimento;
- preenche resumo, sistema, tipo de atividade, status e detalhes;
- envia os chamados;
- captura o número gerado;
- registra sucesso, erro ou necessidade de verificação em um arquivo de resultado;
- possui modo de teste para preencher o primeiro registro sem enviar.

## Tecnologias

- Python 3
- Selenium
- Pandas
- Google Chrome / ChromeDriver

## Estrutura sugerida

```text
.
├── automacao_chamados.py
├── data/
│   └── chamados_exemplo.csv
├── resultados/
├── .gitignore
└── README.md
```

## Configuração

A URL e o caminho do CSV podem ser definidos por variáveis de ambiente:

```text
MAXIMO_URL=https://seu-ambiente/maximo/ui/login
CHAMADOS_CSV=data/chamados.csv
```

Ou alterados diretamente no arquivo, desde que nenhuma informação interna ou credencial seja versionada.

## Formato do CSV

O arquivo precisa conter, no mínimo, as colunas:

- `Título`
- `Detalhes`
- `Solução`

Exemplo:

```csv
Título;Detalhes;Solução
Exemplo de atendimento;Descrição do problema;Orientação realizada ao usuário
```

## Segurança

Não versionar:

- senhas;
- tokens;
- cookies ou sessões do navegador;
- arquivos CSV reais contendo dados de usuários ou chamados;
- URLs internas que não possam ser divulgadas;
- caminhos locais da máquina de trabalho;
- logs contendo dados pessoais ou informações internas.

Use `.gitignore` para impedir o envio acidental desses arquivos.

## Modo de teste

Antes de realizar envios reais, altere:

```python
MODO_TESTE = True
```

Nesse modo, o primeiro registro é preenchido no navegador, mas não é enviado.

## Aviso

Este projeto é uma automação de navegador. A implementação deve ser utilizada somente em sistemas nos quais o usuário tenha autorização para automatizar as tarefas. O uso em ambiente corporativo deve seguir as políticas de segurança, privacidade e automação da organização.
