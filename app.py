import streamlit as st
import requests
import json
import sqlite3
import re
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Zamboni & Giron — Sourcing & Licitações",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# DESIGN SYSTEM: DALA STYLE REFERENCE (BLACK VOID & ELECTRIC IRIS)
# ==============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@200;400;600;700&display=swap');

:root {
    --color-void: #000000;
    --color-bone-white: #ffffff;
    --color-ash-gray: #9a9a9a;
    --color-silver-mist: #bdbdbd;
    --color-electric-iris: #8052ff;
    --color-saffron-spark: #ffb829;
    --color-deep-verdant: #15846e;
    --font-stack: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* Global App Surface */
.stApp {
    background-color: var(--color-void) !important;
    color: var(--color-bone-white) !important;
    font-family: var(--font-stack) !important;
}

/* Header & Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-stack) !important;
    font-weight: 400 !important;
    color: var(--color-bone-white) !important;
    letter-spacing: -0.04em !important;
}

h1 {
    font-size: 56px !important;
    line-height: 1.05 !important;
    letter-spacing: -2.2px !important;
    margin-bottom: 8px !important;
}

h2 {
    font-size: 32px !important;
    letter-spacing: -1.2px !important;
    margin-top: 24px !important;
}

h3 {
    font-size: 20px !important;
    letter-spacing: -0.6px !important;
    color: var(--color-bone-white) !important;
}

p, span, label {
    font-family: var(--font-stack) !important;
    font-weight: 200 !important;
    color: var(--color-silver-mist) !important;
    font-size: 16px !important;
    line-height: 1.5 !important;
}

/* Accent Labels */
.zg-tag-amber {
    font-family: var(--font-stack) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: var(--color-saffron-spark) !important;
    margin-bottom: 6px !important;
    display: inline-block;
}

.zg-tag-iris {
    font-family: var(--font-stack) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: var(--color-electric-iris) !important;
}

/* Buttons: Electric Iris Pill */
.stButton > button {
    background-color: var(--color-electric-iris) !important;
    color: var(--color-bone-white) !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 12px 28px !important;
    font-family: var(--font-stack) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    background-color: #6b3ee3 !important;
    color: #ffffff !important;
    transform: translateY(-1px);
}

/* Inputs & Textareas */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background-color: #0d0d0d !important;
    color: var(--color-bone-white) !important;
    border: 1px solid #1f1f1f !important;
    border-radius: 16px !important;
    font-family: var(--font-stack) !important;
    font-weight: 400 !important;
    font-size: 15px !important;
    padding: 14px 18px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--color-electric-iris) !important;
    box-shadow: 0 0 0 1px var(--color-electric-iris) !important;
}

/* Clean Metric Blocks */
.zg-metric-card {
    padding: 18px 0px;
    border-bottom: 1px solid #161616;
}

.zg-metric-val {
    font-size: 26px;
    font-weight: 400;
    color: #ffffff;
    letter-spacing: -0.8px;
    margin-top: 4px;
}

.zg-link-card {
    padding: 16px 0;
    border-bottom: 1px solid #141414;
}

.zg-link-title {
    font-size: 16px;
    font-weight: 400;
    color: #ffffff !important;
    text-decoration: none;
}

.zg-link-title:hover {
    color: var(--color-saffron-spark) !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ==============================================================================
# BANCO DE DADOS LOCAL (COMPARTILHADO)
# ==============================================================================
def init_db():
    conn = sqlite3.connect("sourcing_zamboni.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            usuario TEXT,
            item_bruto TEXT,
            part_number TEXT,
            fabricante TEXT,
            ncm TEXT,
            status_linha TEXT,
            menor_preco REAL,
            link_compra TEXT,
            distribuidor_contato TEXT,
            tipo_importado TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_cotacao(usuario, item_bruto, pn, fab, ncm, status, preco, link, contato, tipo_imp):
    conn = sqlite3.connect("sourcing_zamboni.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO cotacoes (data_hora, usuario, item_bruto, part_number, fabricante, ncm, status_linha, menor_preco, link_compra, distribuidor_contato, tipo_importado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%d/%m/%Y %H:%M"), usuario, item_bruto, pn, fab, ncm, status, preco, link, contato, tipo_imp))
    conn.commit()
    conn.close()

def listar_historico():
    conn = sqlite3.connect("sourcing_zamboni.db")
    c = conn.cursor()
    c.execute("SELECT data_hora, usuario, part_number, fabricante, ncm, menor_preco, status_linha, link_compra FROM cotacoes ORDER BY id DESC LIMIT 20")
    dados = c.fetchall()
    conn.close()
    return dados

init_db()

# ==============================================================================
# AUTENTICAÇÃO DOS SÓCIOS
# ==============================================================================
USUARIOS_SISTEMA = {
    "ivo": "zamboni2026",
    "socio": "distribuidora2026",
    "admin": "zamboni123"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

if not st.session_state["autenticado"]:
    st.markdown('<div class="zg-tag-amber">ZAMBONI & GIRON — DISTRIBUIÇÃO INDUSTRIAL</div>', unsafe_allow_html=True)
    st.markdown("<h1>Sourcing Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p>Ambiente seguro para pesquisa automatizada de cotações, NCM, estoque e distribuidores.</p>", unsafe_allow_html=True)
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    col_l1, col_l2 = st.columns()
    with col_l1:
        user_input = st.text_input("Usuário:", placeholder="ex: ivo")
        pass_input = st.text_input("Senha:", type="password", placeholder="••••••••")
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        if st.button("ACESSAR SISTEMA"):
            if user_input.lower() in USUARIOS_SISTEMA and USUARIOS_SISTEMA[user_input.lower()] == pass_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = user_input.lower()
                st.rerun()
            else:
                st.error("Credenciais inválidas. Tente novamente.")
    st.stop()

# ==============================================================================
# MOTOR DE INTELIGÊNCIA & APIS GRATUITAS
# ==============================================================================
def extrair_metadados(texto):
    texto_limpo = texto.strip()
    
    pn_match = re.search(r'\b([A-Z0-9]{3,}[-/.][A-Z0-9/-]+|[A-Z]{2,}\d{3,}[A-Z0-9]*)\b', texto_limpo, re.IGNORECASE)
    part_number = pn_match.group(0).upper() if pn_match else "NÃO ESPECIFICADO"
    
    marcas = ["SCHNEIDER", "WEG", "SIEMENS", "TELEMECANIQUE", "SWAGELOK", "DANFOSS", "PADO", "BURNDY", "ABB", "FLUKE", "3M", "TRAMONTINA", "DEWALT", "BOSCH", "PARKER", "FESTO", "SMC", "EUROSUL", "QUALITY FIX"]
    fabricante = "GENÉRICO / MULTIMARCA"
    for m in marcas:
        if m in texto_limpo.upper():
            fabricante = m
            break
            
    specs = []
    if "INOX" in texto_limpo.upper() or "AI316" in texto_limpo.upper():
        specs.append("Aço Inox (AI-316/304)")
    if "24V" in texto_limpo.upper() or "220V" in texto_limpo.upper():
        specs.append("Tensão Específica")
    if "JIC" in texto_limpo.upper() or "NPT" in texto_limpo.upper():
        specs.append("Padrão Rosca/Conexão")

    return {
        "part_number": part_number,
        "fabricante": fabricante,
        "especificacoes": specs
    }

def consultar_ncm_brasilapi(termo):
    try:
        url = f"https://brasilapi.com.br/api/ncm/v1?search={termo}"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            itens = res.json()
            if itens and len(itens) > 0:
                return itens[0].get("codigo"), itens[0].get("descricao")
    except:
        pass
    return "8479.89.99", "Outras máquinas e aparelhos mecânicos com função própria"

def buscar_mercado_livre(termo_busca):
    try:
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={termo_busca}&limit=4"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            produtos = []
            for r in results:
                produtos.append({
                    "titulo": r.get("title"),
                    "preco": r.get("price", 0.0),
                    "link": r.get("permalink"),
                    "estoque": r.get("available_quantity", 0),
                    "frete_gratis": r.get("shipping", {}).get("free_shipping", False)
                })
            return produtos
    except:
        pass
    return []

def avaliar_ciclo_e_origem(fabricante, pn):
    marcas_nacionais = ["WEG", "SCHNEIDER", "SIEMENS", "PADO", "TRAMONTINA", "TELEMECANIQUE", "ABB", "DANFOSS", "3M", "BURNDY"]
    
    status_linha = "🟢 EM LINHA (ATIVO)"
    substituto = None
    if pn != "NÃO ESPECIFICADO" and any(x in pn for x in ["-OLD", "EOL", "DESCON"]):
        status_linha = "🟡 DESCONTINUADO / OBSOLETO"
        substituto = f"{pn}-NOVA-GERACAO"
        
    if fabricante in marcas_nacionais:
        tipo_origem = "Nacional / Distribuição Oficial no BR"
        facilidade_importado = "🟢 FÁCIL ACESSO (Pronta Entrega BR)"
    else:
        tipo_origem = "Estrangeiro / Importação Direta"
        facilidade_importado = "⚠️ ACESSO MODERADO (Verificar Lead Time)"

    return status_linha, substituto, tipo_origem, facilidade_importado

# ==============================================================================
# INTERFACE PRINCIPAL DO SISTEMA
# ==============================================================================
col_h1, col_h2 = st.columns()
with col_h1:
    st.markdown('<div class="zg-tag-amber">PORTAL DE LICITAÇÕES & SUPRIMENTOS</div>', unsafe_allow_html=True)
    st.markdown("<h1>Zamboni & Giron</h1>", unsafe_allow_html=True)
    st.markdown("<p>Pesquisa automatizada de itens, NCM fiscal, links com estoque, distribuidores e análise de importados.</p>", unsafe_allow_html=True)

with col_h2:
    st.markdown(f"<div style='text-align: right; padding-top: 15px;'><span class='zg-tag-iris'>OPERADOR: {st.session_state['usuario'].upper()}</span></div>", unsafe_allow_html=True)
    if st.button("DESCONECTAR", key="logout"):
        st.session_state["autenticado"] = False
        st.rerun()

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

tab_pesquisa, tab_historico, tab_diretorio = st.tabs(["⚡ NOVA PESQUISA", "📂 HISTÓRICO COMPARTILHADO", "🏭 DISTRIBUIDORES"])

with tab_pesquisa:
    col_in1, col_in2 = st.columns()
    with col_in1:
        raw_text = st.text_area(
            "Descrição do Item (Petronect / Compras.gov.br / Edital):",
            placeholder="Exemplo: AQUISIÇÃO DE JOGO DE CONTATO PARA CONTATOR TELEMECANIQUE PN: LC1D25B7 TENSÃO 24V QTD: 50 UNIDADES",
            height=100
        )
    with col_in2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        btn_pesquisar = st.button("⚡ EXECUTAR SOURCING", use_container_width=True)

    if btn_pesquisar and raw_text:
        with st.spinner("Varrendo catálogos, Receita Federal, estoques e distribuidores..."):
            meta = extrair_metadados(raw_text)
            ncm_code, ncm_desc = consultar_ncm_brasilapi(meta["fabricante"] if meta["fabricante"] != "GENÉRICO / MULTIMARCA" else "conector")
            status_linha, substituto, tipo_origem, facilidade_imp = avaliar_ciclo_e_origem(meta["fabricante"], meta["part_number"])
            produtos_ml = buscar_mercado_livre(f"{meta['fabricante']} {meta['part_number']}".strip())

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("---")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="zg-tag-amber">PART NUMBER & MARCA</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='zg-metric-val'>{meta['part_number']}</div>", unsafe_allow_html=True)
            st.caption(f"Fabricante: {meta['fabricante']}")
            
        with c2:
            st.markdown('<div class="zg-tag-amber">CLASSIFICAÇÃO FISCAL</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='zg-metric-val'>{ncm_code}</div>", unsafe_allow_html=True)
            st.caption(ncm_desc[:45] + "...")
            
        with c3:
            st.markdown('<div class="zg-tag-amber">STATUS DO PRODUTO</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='zg-metric-val'>{status_linha}</div>", unsafe_allow_html=True)
            st.caption(f"Substituto: {substituto}" if substituto else "Item ativo em linha")
                
        with c4:
            st.markdown('<div class="zg-tag-amber">VIABILIDADE LOGÍSTICA</div>', unsafe_allow_html=True)
            st.markdown(f"<div class='zg-metric-val'>{facilidade_imp}</div>", unsafe_allow_html=True)
            st.caption(tipo_origem)

        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        
        col_res1, col_res2 = st.columns()
        
        with col_res1:
            st.markdown("### 🛒 Links de Compra com Estoque Aberto")
            if produtos_ml:
                for p in produtos_ml:
                    st.markdown(f"""
                    <div class="zg-link-card">
                        <a href="{p['link']}" target="_blank" class="zg-link-title">🔗 {p['titulo']}</a><br>
                        <span style="color: #ffffff; font-weight: 600; font-size: 18px;">R$ {p['preco']:,.2f}</span>
                        <span style="color: #9a9a9a; margin-left: 15px;">Estoque: <strong>{p['estoque']} un</strong></span>
                        <span style="color: #15846e; margin-left: 10px;">{'🚚 Frete Grátis' if p['frete_gratis'] else ''}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Nenhum anúncio direto com estoque imediato em marketplace aberto.")
                
            termo_google = f"{meta['fabricante']} {meta['part_number']} distribuidor estoque brasil"
            google_link = f"https://www.google.com.br/search?q={termo_google.replace(' ', '+')}"
            st.markdown(f"<br><a href='{google_link}' target='_blank' style='color: var(--color-electric-iris); font-weight: 600;'>🔍 Abrir Busca Completa no Google &rarr;</a>", unsafe_allow_html=True)

        with col_res2:
            st.markdown("### 🏭 Contatos de Distribuidores Nacionais")
            st.markdown(f"""
            <div style="background-color: #0a0a0a; padding: 20px; border-radius: 16px; border: 1px solid #161616;">
                <span class="zg-tag-amber">CANAL COMERCIAL HOMOLOGADO</span>
                <p style="color: #ffffff; font-weight: 400; font-size: 16px; margin: 4px 0;"><strong>Fabricante:</strong> {meta['fabricante']}</p>
                <p style="color: #bdbdbd; font-size: 14px; margin: 2px 0;"><strong>Canal Oficial Brasil:</strong> Televendas / Engenharia de Aplicação</p>
                <p style="color: #bdbdbd; font-size: 14px; margin: 2px 0;"><strong>Região de Atendimento:</strong> Sudeste / Espírito Santo</p>
                <p style="color: #bdbdbd; font-size: 14px; margin: 2px 0;"><strong>E-mail Sugerido:</strong> vendas.corporativas@{meta['fabricante'].lower().replace(' ', '')}.com.br</p>
            </div>
            """, unsafe_allow_html=True)
            
            rfq_template = f"""Prezados,

Somos da ZAMBONI & GIRON COMERCIO E DISTRIBUICAO LTDA (CNPJ: 58.305.267/0001-77).
Solicitamos cotação de preços para revenda do item abaixo com entrega no Espírito Santo:

• Fabricante: {meta['fabricante']}
• Part Number / Ref: {meta['part_number']}
• Descrição: {raw_text}
• NCM: {ncm_code}

Favor informar:
1. Menor preço unitário com impostos destacados (IPI / ICMS)
2. Prazo de faturamento (preferência 30 dias)
3. Prazo de entrega CIF e envio da Ficha Técnica (Datasheet)

Atenciosamente,
Departamento de Suprimentos — Zamboni & Giron
zambonigirondistribuidora@gmail.com | (27) 99706-9911
"""
            with st.expander("✉️ VER MODELO DE E-MAIL DE COTAÇÃO (RFQ)"):
                st.text_area("Copie o texto para envio ao fornecedor:", rfq_template, height=180)

        menor_p = produtos_ml[0]["preco"] if produtos_ml else 0.0
        link_p = produtos_ml[0]["link"] if produtos_ml else ""
        salvar_cotacao(
            st.session_state["usuario"],
            raw_text,
            meta["part_number"],
            meta["fabricante"],
            ncm_code,
            status_linha,
            menor_p,
            link_p,
            meta["fabricante"],
            facilidade_imp
        )
        st.success("✅ Cotação registrada no histórico compartilhado!")

with tab_historico:
    st.markdown("### 📂 Histórico de Cotações Compartilhado")
    historico = listar_historico()
    if historico:
        for h in historico:
            data, user, pn, fab, ncm, preco, status, link = h
            st.markdown(f"""
            <div class="zg-metric-card">
                <span class="zg-tag-amber">{data} • Operador: {user.upper()}</span>
                <div style="font-size: 18px; font-weight: 400; color: #ffffff; margin: 4px 0;">
                    <strong>{fab}</strong> — PN: {pn} | <span style="color: #8052ff;">NCM: {ncm}</span>
                </div>
                <div style="font-size: 14px; color: #9a9a9a;">
                    Status: {status} | Menor Preço: <strong>R$ {preco:,.2f}</strong>
                    {f"| <a href='{link}' target='_blank' style='color: #ffb829;'>Abrir Link de Compra</a>" if link else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma cotação pesquisada ainda.")

with tab_diretorio:
    st.markdown("### 🏭 Diretório de Fabricantes & Distribuidores Homologados")
    fornecedores = [
        {"nome": "Schneider Electric / Telemecanique", "tipo": "Elétrica & Automação", "contato": "0800 7289 500 / schneider-electric.com.br", "status": "Nacional / Filial SP"},
        {"nome": "WEG S/A", "tipo": "Motores, Drives e Contatores", "contato": "(47) 3276-4000 / weg.net", "status": "Fabricante Nacional"},
        {"nome": "Swagelok Brasil (Tecflux)", "tipo": "Válvulas & Conexões Inox / JIC", "contato": "(11) 5080-8800 / swagelok.com.br", "status": "Distribuidor Master BR"},
        {"nome": "Siemens Brasil", "tipo": "Instrumentação & Chaves", "contato": "0800 119 463 / siemens.com.br", "status": "Filial Nacional"},
        {"nome": "Pado S/A", "tipo": "Cadeados & Fechaduras Inox", "contato": "0800 701 4224 / pado.com.br", "status": "Fabricante Nacional"}
    ]
    for f in fornecedores:
        st.markdown(f"""
        <div class="zg-metric-card">
            <span class="zg-tag-iris">{f['tipo']}</span>
            <div style="font-size: 18px; font-weight: 400; color: #ffffff; margin: 4px 0;">{f['nome']}</div>
            <div style="font-size: 14px; color: #bdbdbd;">Contato: {f['contato']} | <strong>{f['status']}</strong></div>
        </div>
        """, unsafe_allow_html=True)
