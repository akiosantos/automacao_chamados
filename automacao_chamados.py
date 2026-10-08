import os

import re

import time

import unicodedata

from datetime import datetime



import pandas as pd



from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import (

    TimeoutException,

    StaleElementReferenceException,

)





\# ============================================================

\# CONFIGURAÇÕES

\# ============================================================



URL_MAXIMO = "https://seu-ambiente/maximo/ui/login"



FILE_NAME = r"C:**\U**ser&#x73;**\l**ucas.***&#x6F;**\O**neDrive - Softplan\Documentos\Abrir Chamado&#x73;**\c**hamados.csv"



\# Valores fixos de todos os chamados

SISTEMA = "Solar BPM"

STATUS = "Resolvido"



\# Trecho do texto da opção "1) Atendimento de 1º nível".

TRECHO_TIPO_ATIVIDADE = "tendimento de 1"



\# Linha da planilha onde começar (2 = primeira linha depois do cabeçalho).

\# Só mude se o script parar no meio e você quiser continuar de onde parou.

INICIAR_NA_LINHA = 2



\# True  = preenche SOMENTE a 1ª linha, NÃO envia e espera você conferir.

\# False = envia de verdade.

MODO_TESTE = False



TIMEOUT = 20





\# ============================================================

\# FUNÇÕES AUXILIARES - MAXIMO

\# ============================================================



def aguardar_maximo(driver, timeout=TIMEOUT):

    """Espera o Maximo terminar de processar após cada clique/TAB."""

    time.sleep(0.5)

    fim = time.time() + timeout



    while time.time() < fim:

        try:

            ocupado = driver.execute_script("""

                if (document.readyState !== 'complete') return true;

                var w = document.getElementById('wait');

                if (w && w\.offsetParent !== null) return true;

                return false;

            """)

            if not ocupado:

                return

        except Exception:

            pass

        time.sleep(0.3)





def achar_visivel(driver, xpath, timeout=TIMEOUT):

    """Retorna o primeiro elemento VISÍVEL que bate com o XPath."""



    def \_procurar(d):

        for el in d.find_elements(By.XPATH, xpath):

            try:

                if el.is_displayed():

                    return el

            except StaleElementReferenceException:

                pass

        return False



    return WebDriverWait(driver, timeout).until(\_procurar)





def existe_visivel(driver, xpath, timeout=2):

    try:

        achar_visivel(driver, xpath, timeout)

        return True

    except TimeoutException:

        return False





def clicar(driver, elemento):

    try:

        elemento.click()

    except Exception:

        driver.execute_script("arguments[0].click();", elemento)





def campo_por_label(driver, texto, timeout=TIMEOUT):

    """Localiza um campo pelo TEXTO do label (ex.: 'Sistema')."""

    xpaths = [

        f"//label[normalize-space(.)='{texto}']",

        f"//label[contains(normalize-space(.), '{texto}')]",

    ]



    def \_procurar(d):

        for xpath in xpaths:

            for label in d.find_elements(By.XPATH, xpath):

                try:

                    if not label.is_displayed():

                        continue

                    alvo = label.get_attribute("for")

                    if not alvo:

                        continue

                    for el in d.find_elements(By.ID, alvo):

                        if el.is_displayed():

                            return el

                except StaleElementReferenceException:

                    pass

        return False



    try:

        return WebDriverWait(driver, timeout).until(\_procurar)

    except TimeoutException:

        raise Exception(f"Campo '{texto}' não encontrado na tela.")





def mensagem_maximo(driver, timeout=1):

    """Retorna o texto de uma mensagem BMXAA visível (se houver)."""

    try:

        el = achar_visivel(driver, "//\*[contains(text(), 'BMXAA')]", timeout)

        return el.text.strip()

    except TimeoutException:

        return ""





def fechar_popup_ok(driver):

    """Clica em 'OK' se houver uma janela de mensagem aberta."""

    xpath = (

        "//\*[self::button or @role='button' or self::a]"

        "[normalize-space(.)='OK']"

    )

    if existe_visivel(driver, xpath, timeout=1):

        clicar(driver, achar_visivel(driver, xpath))

        aguardar_maximo(driver)





def verificar_erro(driver, contexto):

    """Mensagens de ERRO do Maximo terminam com 'E' (ex.: BMXAA4211E)."""

    msg = mensagem_maximo(driver)

    if re.search(r"BMXAA\d+E", msg):

        fechar_popup_ok(driver)

        raise Exception(f"{contexto}: {msg}")





def preencher_texto(driver, campo, valor):

    clicar(driver, campo)

    campo.send_keys(Keys.CONTROL, "a")

    campo.send_keys(Keys.DELETE)

    campo.send_keys(valor)

    campo.send_keys(Keys.TAB)

    aguardar_maximo(driver)





def preencher_lookup(driver, label, valor):

    """Campos com lupa: digita o valor e dá TAB para o Maximo validar."""

    preencher_texto(driver, campo_por_label(driver, label), valor)

    verificar_erro(driver, f"Valor '{valor}' recusado em '{label}'")



    valor_final = campo_por_label(driver, label).get_attribute("value")

    if not valor_final:

        raise Exception(f"O campo '{label}' ficou vazio após digitar '{valor}'.")



    print(f"{label}: {valor_final}")





def selecionar_combo(driver, label, trecho):

    """Campos com setinha (lista suspensa)."""

    campo = campo_por_label(driver, label)

    clicar(driver, campo)

    aguardar_maximo(driver)



    try:

        opcao = achar_visivel(

            driver,

            f"//\*[contains(normalize-space(text()), '{trecho}')]",

            timeout=5,

        )

    except TimeoutException:

        raise Exception(

            f"Opção contendo '{trecho}' não apareceu na lista de '{label}'."

        )



    clicar(driver, opcao)

    aguardar_maximo(driver)



    valor_final = campo_por_label(driver, label).get_attribute("value")

    print(f"{label}: {valor_final}")



    if trecho.lower() not in (valor_final or "").lower():

        raise Exception(f"'{label}' não ficou com a opção esperada.")





def preencher_detalhes(driver, texto):

    try:

        campo = campo_por_label(driver, "Detalhes", timeout=5)

    except Exception:

        caixas = [

            t for t in driver.find_elements(By.TAG_NAME, "textarea")

            if t.is_displayed()

        ]

        if not caixas:

            raise Exception("Campo 'Detalhes' não encontrado.")

        campo = caixas[-1]



    preencher_texto(driver, campo, texto)





XPATH_LINK_N1 = "//\*[normalize-space(text())='Suporte Local N1']"

XPATH_FORMULARIO = "//\*[normalize-space(text())='Detalhes da Solicitação']"





def formulario_aberto(driver):

    return existe_visivel(driver, XPATH_FORMULARIO, timeout=1)





def garantir_pagina_n1(driver):

    """Garante que estamos na tela com o botão 'Suporte Local N1'."""

    if existe_visivel(driver, XPATH_LINK_N1, timeout=3):

        return



    print("Voltando para 'Suporte Equipe Local'...")

    link = achar_visivel(

        driver, "//\*[normalize-space(text())='Suporte Equipe Local']"

    )

    clicar(driver, link)

    aguardar_maximo(driver)

    achar_visivel(driver, XPATH_LINK_N1)





def abrir_formulario(driver):

    clicar(driver, achar_visivel(driver, XPATH_LINK_N1))

    aguardar_maximo(driver)

    achar_visivel(driver, XPATH_FORMULARIO)

    print("Formulário 'Suporte Local N1' aberto.")





def fechar_formulario(driver):

    """Fecha o formulário sem enviar (usado em erro e no modo teste)."""

    try:

        fechar_popup_ok(driver)

        if not formulario_aberto(driver):

            return



        xpath_cancelar = (

            "//\*[self::button or @role='button' or self::a]"

            "[normalize-space(.)='Cancelar']"

        )

        if existe_visivel(driver, xpath_cancelar, timeout=2):

            clicar(driver, achar_visivel(driver, xpath_cancelar))

        else:

            driver.switch_to.active_element.send_keys(Keys.ESCAPE)



        aguardar_maximo(driver)

    except Exception:

        pass





def botao_enviar(driver):

    xpath = (

        "//\*[self::button or @role='button' or self::a]"

        "[contains(normalize-space(.), 'Enviar')]"

        " | //input[@type='button' or @type='submit']"

        "[contains(@value, 'Enviar')]"

    )

    return achar_visivel(driver, xpath)





def capturar_numero_chamado(driver, timeout=TIMEOUT):

    """

    Lê a janela 'Solicitação Submetida':

    'A Solicitação de Serviço 670156 foi criada.'

    """

    el = achar_visivel(driver, "//\*[contains(text(), 'foi criada')]", timeout)

    texto = el.text.strip()



    encontrado = re.search(r"(\d{5,})", texto)

    numero = encontrado.group(1) if encontrado else ""



    return numero, texto





\# ============================================================

\# LEITURA DO CSV

\# ============================================================



def normalizar(texto):

    """'Título' -> 'titulo', 'SOLUÇÃO' -> 'solucao' (sem acento e minúsculo)."""

    texto = unicodedata.normalize("NFKD", str(texto))

    texto = "".join(c for c in texto if not unicodedata.combining(c))

    return texto.strip().lower()





def ler_planilha(caminho):

    """Detecta sozinho a codificação (UTF-8 ou ANSI) e o separador (; ou ,)."""

    for codificacao in ("utf-8-sig", "cp1252"):

        try:

            with open(caminho, encoding=codificacao) as arquivo:

                cabecalho = arquivo.readline()



            separador = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","



            return pd.read_csv(

                caminho, sep=separador, encoding=codificacao, dtype=str

            )

        except UnicodeDecodeError:

            continue



    raise Exception("Não foi possível ler a planilha.")





df = ler_planilha(FILE_NAME).fillna("")

df.columns = df.columns.str.strip()



colunas = {normalizar(c): c for c in df.columns}



for nome in ["titulo", "detalhes", "solucao"]:

    if nome not in colunas:

        raise Exception(

            f"A coluna '{nome}' não existe na planilha.\n"

            f"Colunas encontradas: {list(df.columns)}"

        )



col_titulo = colunas["titulo"]

col_detalhes = colunas["detalhes"]

col_solucao = colunas["solucao"]





def montar_detalhes(linha):

    detalhes = linha[col_detalhes].strip()

    solucao = linha[col_solucao].strip()



    partes = []

    if detalhes:

        partes.append(f"Detalhes:\n{detalhes}")

    if solucao:

        partes.append(f"Solução:\n{solucao}")



    return "\n\n".join(partes)





df["Resumo"] = df[col_titulo].str.strip()

df["Detalhes"] = df.apply(montar_detalhes, axis=1)



\# Linha do Excel (linha 1 = cabeçalho)

df["Linha"] = df.index + 2



\# Ignora linhas totalmente vazias (comuns no fim de CSV exportado)

df = df[(df["Resumo"] != "") | (df["Detalhes"] != "")]



\# Começa na linha configurada

df = df[df["Linha"] >= INICIAR_NA_LINHA]



print("\n========================================")

print("        CHAMADOS PARA ABERTURA")

print("========================================\n")

for \_, r in df.iterrows():

    print(f"Linha {r['Linha']}: {r['Resumo']}")

print("\nQuantidade de chamados:", len(df))



if df.empty:

    print("\nNenhum chamado para abrir.")

    exit()





\# ============================================================

\# ARQUIVO DE RESULTADO (um novo a cada execução)

\# ============================================================



ARQUIVO_RESULTADO = os.path.join(

    os.path.dirname(FILE_NAME),

    f"resultado_chamados\_{datetime.now().strftime('%Y-%m-%d\_%H-%M')}.csv"

)



resultados = []





def salvar_resultado(num_linha, resumo, status, chamado, mensagem):

    resultados.append({

        "Linha": num_linha,

        "Resumo": resumo,

        "Status": status,

        "Chamado": chamado,

        "Mensagem": mensagem,

        "DataHora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),

    })

    pd.DataFrame(resultados).to_csv(

        ARQUIVO_RESULTADO, sep=";", index=False, encoding="utf-8-sig"

    )





\# ============================================================

\# ABRIR CHROME E LOGIN MANUAL

\# ============================================================



options = Options()

options.add_argument("--start-maximized")

driver = webdriver.Chrome(options=options)



driver.get(URL_MAXIMO)



print("\n========================================")

print("             ATENÇÃO")

print("========================================")

print()

print("1. Faça login no Maximo.")

print("2. Vá em Auto-atendimento > Centro de Autoatendimento")

print("   > Solicitar um Novo Serviço > Suporte Equipe Local.")

print("3. Quando aparecer o botão 'Suporte Local N1',")

print("   volte aqui e pressione ENTER.")

print()

print("========================================")



input("Pressione ENTER quando estiver na tela...")



if MODO_TESTE:

    print("\n\*\*\* MODO TESTE: só a 1ª linha, SEM enviar. \*\*\*")

else:

    print(f"\nSerão abertos {len(df)} chamado(s).")

    confirmacao = input("Digite ABRIR para iniciar o envio: ")

    if confirmacao.strip().upper() != "ABRIR":

        print("\nProcessamento cancelado pelo usuário.")

        driver.quit()

        exit()





\# ============================================================

\# PROCESSAR CADA LINHA

\# ============================================================



total = len(df)



for posicao, (\_, linha) in enumerate(df.iterrows(), start=1):



    num_linha = linha["Linha"]

    resumo = linha["Resumo"].strip()

    detalhes = linha["Detalhes"].strip()



    print("\n\n========================================")

    print(f" LINHA {num_linha}  ({posicao} de {total})")

    print("========================================")

    print(f"Resumo: {resumo}")



    if not resumo or not detalhes:

        print("Resumo ou Detalhes vazio. Pulando.")

        salvar_resultado(num_linha, resumo, "ERRO", "", "Resumo ou Detalhes vazio.")

        continue



    status = "ERRO"

    chamado = ""

    mensagem = ""

    enviou = False



    try:

        garantir_pagina_n1(driver)

        abrir_formulario(driver)



        preencher_texto(driver, campo_por_label(driver, "Resumo"), resumo)

        preencher_lookup(driver, "Sistema", SISTEMA)

        selecionar_combo(driver, "Tipo de atividade", TRECHO_TIPO_ATIVIDADE)

        preencher_lookup(driver, "Status", STATUS)

        preencher_detalhes(driver, detalhes)



        print("Formulário preenchido.")



        if MODO_TESTE:

            input(

                "\nMODO TESTE: confira o formulário no navegador.\n"

                "Pressione ENTER para FECHAR sem enviar..."

            )

            fechar_formulario(driver)

            status = "TESTE"

            mensagem = "Preenchido e fechado sem enviar."



        else:

            clicar(driver, botao_enviar(driver))

            enviou = True

            print("Clique em Enviar realizado.")

            aguardar_maximo(driver)



            verificar_erro(driver, "Maximo recusou o envio")



            try:

                chamado, mensagem = capturar_numero_chamado(driver)

            except TimeoutException:

                raise Exception(

                    "A mensagem 'foi criada' não apareceu após o envio."

                )



            fechar_popup_ok(driver)



            if formulario_aberto(driver):

                raise Exception("O formulário continuou aberto após o envio.")



            status = "SUCESSO"

            print(f"Chamado aberto! Nº {chamado}")



    except Exception as erro:

        # Se já clicou em Enviar, o chamado PODE ter sido criado.

        status = "VERIFICAR" if enviou else "ERRO"

        mensagem = str(erro).strip().splitlines()[0][:300]



        print(f"\n{status}: {mensagem}")

        fechar_formulario(driver)



    salvar_resultado(num_linha, resumo, status, chamado, mensagem)

    print(f"Resultado registrado: {status}")



    if MODO_TESTE:

        break





\# ============================================================

\# RESUMO FINAL

\# ============================================================



df_final = pd.DataFrame(resultados)

contagem = df_final["Status"].value_counts() if not df_final.empty else {}



print("\n\n========================================")

print("       PROCESSAMENTO FINALIZADO")

print("========================================")

for st in ["SUCESSO", "VERIFICAR", "ERRO", "TESTE"]:

    print(f"{st:<10} {contagem.get(st, 0)}")



if not df_final.empty:

    print("\n========================================")

    print("   CHAMADOS (na ordem da planilha)")

    print("========================================")

    for \_, r in df_final.iterrows():

        numero = r["Chamado"] if r["Status"] == "SUCESSO" else r["Status"]

        print(f"Linha {r['Linha']}: {numero}  -  {r['Resumo']}")



print("\nArquivo de resultado:")

print(ARQUIVO_RESULTADO)



input("\nPressione ENTER para fechar o navegador...")

driver.quit()
