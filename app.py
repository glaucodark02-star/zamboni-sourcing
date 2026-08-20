import streamlit as st
import requests
import sqlite3
import re
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO GERAL
# ==============================================================================
st.set_page_config(page_title="Zamboni & Giron — Sourcing", page_icon="⚡", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #000000; color: #ffffff; }
    .stButton > button {
        background-color: #8052ff !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }
    .stButton > button:hover { background-color: #6b3ee3 !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #0d0d0d !important;
        color: #ffffff !important;
        border: 1px solid #222222 !important;
        border-radius: 12px !important;
    }
    .tag-amber { color: #ffb829; font-size: 13px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
    .tag-iris { color: #8052ff; font-size: 13px; font-weight: 600; text-transform: uppercase; }
    .metric-val { font-size: 22px; font-weight: 400; color: #ffffff; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BANCO DE DADOS
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
            link_compra TEXT
        )
    """)
    conn.commit()
    conn.close()

def salvar_cotacao(usuario, item_bruto, pn, fab, ncm, status, preco, link):
    conn = sqlite3.connect("sourcing_zamboni.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO cotacoes (data_hora, usuario, item_bruto, part_number, fabricante, ncm, status_linha, menor_preco, link_compra)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%d/%m/%Y %H:%M"), usuario, item_bruto, pn, fab, ncm, status, preco, link))
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
# AUTENTICAÇÃO
# ==============================================================================
USUARIOS = {
    "ivo": "zamboni2026",
    "socio": "distribuidora2026",
    "admin": "zamboni123"
}

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""

if not st.session_state["autenticado"]:
    st.markdown('<div class="tag-amber">ZAMBONI & GIRON — DISTRIBUIÇÃO INDUSTRIAL</div>', unsafe_allow_html=True)
    st.title("Sourcing Intelligence")
    st.write("Ambiente seguro para pesquisa automatizada de cotações, NCM, estoque e distribuidores.")
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    user_input = st.text_input("Usuário:", placeholder="ex: ivo")
    pass_input = st.text_input("Senha:", type="password", placeholder="••••••••")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("ACESSAR SISTEMA"):
        if user_input.lower() in USUARIOS and USUARIOS[user_input.lower()] == pass_input:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = user_input.lower()
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# ==============================================================================
# MOTOR DE SOURCING
# ==============================================================================
def extrair_dados(texto):
    t = texto.strip()
    pn_match = re.search(r'\b([A-Z0-9]{3,}[-/.][A-Z0-9/-]+|[A-Z]{2,}\d{3,}[A-Z0-9]*)\b', t, re.IGNORECASE)
    pn = pn_match.group(0).upper() if pn_match else "NÃO ESPECIFICADO"
    
    marcas = ["SCHNEIDER", "WEG", "SIEMENS", "TELEMECANIQUE", "SWAGELOK", "DANFOSS", "PADO", "BURNDY", "ABB", "FLUKE", "3M", "TRAMONTINA", "DEWALT", "BOSCH", "PARKER", "FESTO", "SMC", "EUROSUL", "QUALITY FIX"]
    fab = "GENÉRICO / MULTIMARCA"
    for m in marcas:
        if m in t.upper():
            fab = m
            break
            
    return pn, fab

def consultar_ncm(termo):
    try:
        res = requests.get(f"https://brasilapi.com.br/api/ncm/v1?search={termo}", timeout=4)
        if res.status_code == 200 and len(res.json()) > 0:
            return res.json()[0].get("codigo"), res.json()[0].get("descricao")
    except:
        pass
    return "8479.89.99", "Máquinas e aparelhos mecânicos com função própria"

def buscar_estoque_ml(termo):
    try:
        res = requests.get(f"https://api.mercadolibre.com/sites/MLB/search?q={termo}&limit=4", timeout=5)
        if res.status_code == 200:
            results = res.json().get("results", [])
            return [{"titulo": r.get("title"), "preco": r.get("price", 0.0), "link": r.get("permalink"), "estoque": r.get("available_quantity", 0), "frete_gratis": r.get("shipping", {}).get("free_shipping", False)} for r in results]
    except:
        pass
    return []

# ==============================================================================
# PAINEL PRINCIPAL
# ==============================================================================
st.markdown('<div class="tag-amber">PORTAL DE LICITAÇÕES & SUPRIMENTOS</div>', unsafe_allow_html=True)
st.title("Zamboni & Giron")
st.caption("Pesquisa automatizada de itens, NCM fiscal, links com estoque, distribuidores e análise de importados.")
st.markdown(f"<span class='tag-iris'>OPERADOR: {st.session_state['usuario'].upper()}</span>", unsafe_allow_html=True)
if st.button("DESCONECTAR"):
    st.session_state["autenticado"] = False
    st.rerun()

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["⚡ NOVA PESQUISA", "📂 HISTÓRICO COMPARTILHADO", "🏭 DISTRIBUIDORES"])

with tab1:
    raw_text = st.text_area("Descrição do Item (Petronect / Compras.gov.br / Edital):", placeholder="Cole a descrição aqui...", height=80)
    btn_pesquisar = st.button("⚡ PESQUISAR ITEM")

    if btn_pesquisar and raw_text:
        with st.spinner("Pesquisando dados fiscais, catálogos e estoques..."):
            pn, fab = extrair_dados(raw_text)
            ncm_code, ncm_desc = consultar_ncm(fab if fab != "GENÉRICO / MULTIMARCA" else "conector")
            status_linha = "🟢 EM LINHA (ATIVO)" if not any(x in pn for x in ["-OLD", "EOL"]) else "🟡 DESCONTINUADO"
            viabilidade = "🟢 FÁCIL ACESSO (Pronta Entrega BR)" if fab in ["WEG", "SCHNEIDER", "SIEMENS", "PADO", "TRAMONTINA", "TELEMECANIQUE", "ABB", "DANFOSS", "3M", "BURNDY"] else "⚠️ ACESSO MODERADO (Verificar Lead Time)"
            produtos = buscar_estoque_ml(f"{fab} {pn}".strip())

        st.markdown("---")
        st.markdown(f"**Part Number:** {pn} | **Fabricante:** {fab}")
        st.markdown(f"**NCM Oficial:** {ncm_code} ({ncm_desc[:45]}...)")
        st.markdown(f"**Status da Linha:** {status_linha} | **Logística:** {viabilidade}")

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🛒 Links de Compra com Estoque")
        if produtos:
            for p in produtos:
                st.markdown(f"""
                <div style="padding: 10px 0; border-bottom: 1px solid #1a1a1a;">
                    <a href="{p['link']}" target="_blank" style="color: #ffffff; font-size: 15px; font-weight: 500; text-decoration: none;">🔗 {p['titulo']}</a><br>
                    <span style="color: #ffffff; font-weight: 600; font-size: 17px;">R$ {p['preco']:,.2f}</span>
                    <span style="color: #9a9a9a; margin-left: 15px;">Estoque: <strong>{p['estoque']} un</strong></span>
                    <span style="color: #15846e; margin-left: 10px;">{'🚚 Frete Grátis' if p['frete_gratis'] else ''}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Sem estoque imediato em marketplace aberto.")
        
        google_link = f"https://www.google.com.br/search?q={fab}+{pn}+distribuidor+brasil"
        st.markdown(f"<br><a href='{google_link}' target='_blank' style='color: #8052ff; font-weight: 600;'>🔍 Buscar Distribuidores no Google &rarr;</a>", unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🏭 Canal Direto do Fabricante")
        st.markdown(f"""
        <div style="background-color: #0d0d0d; padding: 16px; border-radius: 12px; border: 1px solid #1f1f1f;">
            <span class="tag-amber">CANAL COMERCIAL HOMOLOGADO</span>
            <p style="color: #ffffff; font-size: 15px; margin: 4px 0;"><strong>Fabricante:</strong> {fab}</p>
            <p style="color: #bdbdbd; font-size: 13px; margin: 2px 0;"><strong>Canal Oficial Brasil:</strong> Televendas / Engenharia</p>
            <p style="color: #bdbdbd; font-size: 13px; margin: 2px 0;"><strong>E-mail Sugerido:</strong> vendas.corporativas@{fab.lower().replace(' ', '')}.com.br</p>
        </div>
        """, unsafe_allow_html=True)
        
        rfq = f"""Prezados,\n\nSomos da ZAMBONI & GIRON COMERCIO E DISTRIBUICAO LTDA (CNPJ: 58.305.267/0001-77).\nSolicitamos cotação de preços para revenda do item abaixo com entrega no Espírito Santo:\n\n• Fabricante: {fab}\n• Part Number: {pn}\n• Descrição: {raw_text}\n• NCM: {ncm_code}\n\nFavor informar preço unitário com impostos, prazo de entrega CIF e envio da Ficha Técnica.\n\nAtenciosamente,\nZamboni & Giron | zambonigirondistribuidora@gmail.com"""
        with st.expander("✉️ VER MODELO DE E-MAIL (RFQ)"):
            st.text_area("Copie o texto:", rfq, height=140)

        menor_p = produtos[0]["preco"] if produtos else 0.0
        link_p = produtos[0]["link"] if produtos else ""
        salvar_cotacao(st.session_state["usuario"], raw_text, pn, fab, ncm_code, status_linha, menor_p, link_p)
        st.success("✅ Cotação registrada no histórico compartilhado!")

with tab2:
    st.markdown("### 📂 Histórico de Cotações")
    historico = listar_historico()
    if historico:
        for h in historico:
            data, user, pn, fab, ncm, preco, status, link = h
            st.markdown(f"""
            <div style="padding: 12px 0; border-bottom: 1px solid #1a1a1a;">
                <span class="tag-amber">{data} • Operador: {user.upper()}</span>
                <div style="font-size: 17px; font-weight: 500; color: #ffffff; margin: 2px 0;">
                    <strong>{fab}</strong> — PN: {pn} | <span style="color: #8052ff;">NCM: {ncm}</span>
                </div>
                <div style="font-size: 13px; color: #9a9a9a;">
                    Status: {status} | Menor Preço: <strong>R$ {preco:,.2f}</strong>
                    {f"| <a href='{link}' target='_blank' style='color: #ffb829;'>Abrir Link</a>" if link else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma cotação pesquisada ainda.")

with tab3:
    st.markdown("### 🏭 Diretório de Fabricantes Homologados")
    fornecedores_lista = [
        ("Schneider Electric / Telemecanique", "Elétrica & Automação", "0800 7289 500 / schneider-electric.com.br"),
        ("WEG S/A", "Motores, Drives e Contatores", "(47) 3276-4000 / weg.net"),
        ("Swagelok Brasil (Tecflux)", "Válvulas & Conexões Inox / JIC", "(11) 5080-8800 / swagelok.com.br"),
        ("Siemens Brasil", "Instrumentação & Chaves", "0800 119 463 / siemens.com.br"),
        ("Pado S/A", "Cadeados & Fechaduras Inox", "0800 701 4224 / pado.com.br")
    ]
    for nome, tipo, contato in fornecedores_lista:
        st.markdown(f"""
        <div style="padding: 10px 0; border-bottom: 1px solid #1a1a1a;">
            <span class="tag-iris">{tipo}</span>
            <div style="font-size: 16px; font-weight: 500; color: #ffffff; margin: 2px 0;">{nome}</div>
            <div style="font-size: 13px; color: #bdbdbd;">Contato: {contato}</div>
        </div>
        """, unsafe_allow_html=True)
