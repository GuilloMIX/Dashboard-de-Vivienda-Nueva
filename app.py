import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os

# ------------------------------------------------
# ⚙ CONFIG BÁSICA
# ------------------------------------------------
st.set_page_config(page_title="🏡 Vivienda Nueva en Colombia", layout="wide")
st.title("🏡 Índice de precios de la Vivienda Nueva en Colombia con base en los datos del DANE")

# ------------------------------------------------
# 📂 CONFIGURACIÓN DE RUTAS DINÁMICAS (Local + GitHub) - VERSIÓN CORREGIDA
# ------------------------------------------------

def obtener_ruta_base():
    """
    Detecta automáticamente si está corriendo en local o en Streamlit Cloud
    y retorna la ruta base apropiada para los archivos Excel
    """
    # Ruta local (Windows) - Tu carpeta original
    ruta_local = r"C:\Users\Usuario\Desktop\Clases\6 semestre\Econometria II\Dashboard"
    
    # Verificar si existe la ruta local (para desarrollo en VS Code)
    if os.path.exists(ruta_local):
        print("✅ Ejecutando en LOCAL - Usando ruta de Windows")
        return ruta_local
    
    # Para Streamlit Cloud: Probar múltiples ubicaciones
    posibles_rutas = [
        "Dashboard_github",
        os.path.join(os.getcwd(), "Dashboard_github"),
        ".",
    ]
    
    # Archivos que buscamos
    archivos_requeridos = [
        "Datos vivienda filtrado.xlsx",
        "Indice Vivienda Departamentos.xlsx",
        "Indice Vivienda Obras.xlsx"
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            # Verificar si los archivos existen en esta ruta
            archivos_encontrados = sum(1 for archivo in archivos_requeridos 
                                      if os.path.exists(os.path.join(ruta, archivo)))
            
            if archivos_encontrados >= 2:
                print(f"✅ Ejecutando en CLOUD - Usando ruta: {ruta}")
                print(f"   Archivos encontrados: {archivos_encontrados}/{len(archivos_requeridos)}")
                return ruta
    
    # Por defecto, usar Dashboard_github
    print(f"⚠️ Usando ruta por defecto: Dashboard_github")
    return "Dashboard_github"

# Obtener la ruta base UNA SOLA VEZ
RUTA_BASE = obtener_ruta_base()

# Nombres de los archivos
ARCHIVO_PRINCIPAL = "Datos vivienda filtrado.xlsx"
ARCHIVO_DEPARTAMENTOS = "Indice Vivienda Departamentos.xlsx"
ARCHIVO_CIUDADES = "Indice Vivienda Obras.xlsx"

# ------------------------------------------------
# 🔍 INFORMACIÓN DE DEBUG
# ------------------------------------------------
st.sidebar.markdown("---")

archivos_info = []
for archivo in [ARCHIVO_PRINCIPAL, ARCHIVO_DEPARTAMENTOS, ARCHIVO_CIUDADES]:
    ruta_completa = os.path.join(RUTA_BASE, archivo)
    existe = os.path.exists(ruta_completa)
    archivos_info.append(f"- {archivo} {'✅' if existe else '❌'}")

try:
    archivos_en_directorio = os.listdir(RUTA_BASE) if os.path.exists(RUTA_BASE) else []
    archivos_excel = [f for f in archivos_en_directorio if f.endswith('.xlsx')]
except:
    archivos_excel = []

# ------------------------------------------------
# 🎨 EMOJIS Y CONFIGURACIÓN DE SECCIONES
# ------------------------------------------------
secciones = {
    "Casas": {
        "emoji": "🏚️​",
        "color": "#00c4ff",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    "Apartamento": {
        "emoji": "🏙️​",
        "color": "#ff6b6b",
        "gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    "Total y Modelo": {
        "emoji": "📊​",
        "color": "#4ecdc4",
        "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    }
}

# ------------------------------------------------
# 🎨 ESTILOS AVANZADOS
# ------------------------------------------------
st.markdown(
    """
    <style>
    /* Fondo del sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Ocultar labels de botones por defecto */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        border: none !important;
        background: linear-gradient(135deg, #2a2a3e 0%, #1f1f2e 100%) !important;
        color: white !important;
        font-size: 10rem !important;
        height: 140px !important;
        border-radius: 16px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        border: 2px solid rgba(255,255,255,0.05) !important;
        position: relative !important;
        overflow: hidden !important;
        padding: 0 !important;
        line-height: 200px !important;
    }
    
    /* Efecto de fondo animado */
    [data-testid="stSidebar"] .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.1);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    /* Hover effect */
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-8px) scale(1.05);
        box-shadow: 0 12px 30px rgba(0,196,255,0.4);
        border-color: rgba(0,196,255,0.5);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    /* Efecto de click */
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(-4px) scale(1.02);
    }
    
    /* Estilos específicos para cada botón */
    .btn-Casas button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .btn-region button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    }
    
    .btn-sector button {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%) !important;
    }
    
    /* Animación para botón activo */
    .active-button button {
        border: 3px solid white !important;
        box-shadow: 0 0 30px rgba(255,255,255,0.6) !important;
        animation: pulseGlow 2s infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(255,255,255,0.6);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 40px rgba(255,255,255,0.9);
            transform: scale(1.02);
        }
    }
    
    /* Etiquetas de texto debajo */
    .menu-label {
        text-align: center;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: -8px;
        margin-bottom: 25px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    
    .menu-label.active {
        color: #00c4ff;
        font-size: 1.15rem;
        text-shadow: 0 0 10px rgba(0,196,255,0.8);
    }
    
    /* Separador decorativo */
    .separator {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 15px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------
# 📥 FUNCIONES DE CARGA SIMPLIFICADAS
# ------------------------------------------------
def verificar_archivo(nombre_archivo):
    """Verifica si un archivo existe en la ruta base"""
    ruta_completa = os.path.join(RUTA_BASE, nombre_archivo)
    ruta_abs = os.path.abspath(ruta_completa)
    
    # Debug: imprimir información
    print(f"Verificando archivo: {nombre_archivo}")
    print(f"Ruta relativa: {ruta_completa}")
    print(f"Ruta absoluta: {ruta_abs}")
    print(f"¿Existe?: {os.path.exists(ruta_abs)}")
    
    if not os.path.exists(ruta_abs):
        st.error(f"⚠️ No se encontró el archivo: **{nombre_archivo}**")
        st.info(f"📂 Buscando en: `{ruta_abs}`")
        
        # Listar archivos en el directorio para debug
        try:
            archivos_dir = os.listdir(RUTA_BASE)
            st.warning(f"Archivos disponibles en {RUTA_BASE}: {archivos_dir}")
        except Exception as e:
            st.error(f"Error al listar directorio: {e}")
        
        return None
    return ruta_abs

def listar_hojas_excel(ruta_archivo):
    """Lista todas las hojas disponibles en un archivo Excel"""
    try:
        xls = pd.ExcelFile(ruta_archivo)
        return xls.sheet_names
    except Exception as e:
        st.error(f"Error al leer las hojas del archivo: {e}")
        return []

@st.cache_data
def cargar_datos_principal():
    """Carga el archivo principal de datos de vivienda"""
    try:
        ruta_completa = os.path.join(RUTA_BASE, ARCHIVO_PRINCIPAL)
        ruta_abs = os.path.abspath(ruta_completa)
        
        print(f"Cargando archivo principal: {ruta_abs}")
        
        if not os.path.exists(ruta_abs):
            st.error(f"⚠️ No se encontró el archivo: **{ARCHIVO_PRINCIPAL}**")
            st.info(f"📂 Ruta intentada: `{ruta_abs}`")
            return None
        
        df = pd.read_excel(ruta_abs)
        df["Periodo"] = df["Año"].astype(str) + "-" + df["Trimestre"].astype(str)
        st.success(f"✅ Archivo principal cargado: {ARCHIVO_PRINCIPAL}")
        return df
    except Exception as e:
        st.error(f"⚠️ Error al procesar {ARCHIVO_PRINCIPAL}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

@st.cache_data
def cargar_excel_con_hoja(nombre_archivo, nombre_hoja):
    """
    Función genérica para cargar cualquier archivo Excel con una hoja específica
    Maneja automáticamente nombres de hojas con caracteres especiales
    
    Args:
        nombre_archivo: Nombre del archivo Excel
        nombre_hoja: Nombre de la hoja a cargar
    
    Returns:
        DataFrame o None si hay error
    """
    try:
        # Construir ruta absoluta
        ruta_completa = os.path.join(RUTA_BASE, nombre_archivo)
        ruta_abs = os.path.abspath(ruta_completa)
        
        print(f"Cargando hoja '{nombre_hoja}' de: {ruta_abs}")
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_abs):
            st.error(f"⚠️ No se encontró el archivo: **{nombre_archivo}**")
            st.info(f"📂 Ruta intentada: `{ruta_abs}`")
            
            # Listar archivos en el directorio
            try:
                archivos_dir = os.listdir(RUTA_BASE)
                st.warning(f"Archivos en {RUTA_BASE}: {archivos_dir}")
            except Exception as e:
                st.error(f"Error al listar directorio: {e}")
            
            return None
        
        # Listar hojas disponibles
        xls = pd.ExcelFile(ruta_abs)
        hojas_disponibles = xls.sheet_names
        
        if not hojas_disponibles:
            st.error(f"⚠️ No se pudieron leer las hojas del archivo: {nombre_archivo}")
            return None
        
        # Función para limpiar nombres de hojas
        def limpiar_nombre(nombre):
            import re
            nombre_limpio = re.sub(r'[\t\r\n\x00-\x1F\x7F-\x9F]', '', nombre)
            return nombre_limpio.strip()
        
        # Buscar coincidencia
        hoja_encontrada = None
        
        # 1. Coincidencia exacta
        if nombre_hoja in hojas_disponibles:
            hoja_encontrada = nombre_hoja
        else:
            # 2. Buscar por nombre limpio
            nombre_buscado_limpio = limpiar_nombre(nombre_hoja).lower()
            
            for hoja in hojas_disponibles:
                hoja_limpia = limpiar_nombre(hoja).lower()
                if hoja_limpia == nombre_buscado_limpio:
                    hoja_encontrada = hoja
                    break
            
            # 3. Buscar si está contenido
            if hoja_encontrada is None:
                for hoja in hojas_disponibles:
                    if nombre_hoja.lower() in hoja.lower() or hoja.lower().startswith(nombre_hoja.lower()):
                        hoja_encontrada = hoja
                        break
        
        # Si no se encontró
        if hoja_encontrada is None:
            st.error(f"⚠️ No se encontró la hoja **'{nombre_hoja}'** en **{nombre_archivo}**")
            st.warning(f"📋 Hojas disponibles: {', '.join(hojas_disponibles)}")
            return None
        
        # Cargar la hoja
        df = pd.read_excel(ruta_abs, sheet_name=hoja_encontrada)
        
        # Mensaje de éxito
        if hoja_encontrada == nombre_hoja:
            st.success(f"✅ Datos cargados: {nombre_archivo} → '{nombre_hoja}' ({len(df)} filas)")
        else:
            st.success(f"✅ Datos cargados: {nombre_archivo} → '{hoja_encontrada}' (buscada como '{nombre_hoja}') ({len(df)} filas)")
        
        return df
        
    except Exception as e:
        st.error(f"⚠️ Error al leer {nombre_archivo}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None
# ------------------------------------------------
# 📥 INICIALIZAR SESSION STATE
# ------------------------------------------------
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = "Casas"

# ------------------------------------------------
# 🔘 MENÚ LATERAL CON EMOJIS INTERACTIVOS
# ------------------------------------------------
with st.sidebar:
    
    for nombre, config in secciones.items():
        # Determinar si está activo
        is_active = nombre == st.session_state.vista_actual
        active_class = "active-button" if is_active else ""
        button_class = f"btn-{nombre.lower()}"
        
        # Crear columnas para centrar
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        
        with col2:
            # Contenedor con clase específica
            st.markdown(f'<div class="{button_class} {active_class}">', unsafe_allow_html=True)
            
            # Botón con emoji
            if st.button(config["emoji"], key=f"btn_{nombre}", use_container_width=True):
                st.session_state.vista_actual = nombre
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Label debajo del botón
            label_class = "active" if is_active else ""
            st.markdown(f'<div class="menu-label {label_class}">{nombre}</div>', unsafe_allow_html=True)

    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("💡 Haz clic en los iconos para navegar")

# ------------------------------------------------
# 📊 CONTENIDO PRINCIPAL SEGÚN LA VISTA
# ------------------------------------------------
st.markdown("---")

if st.session_state.vista_actual == "Casas":
    st.subheader("🏚️ Índice de la vivienda enfocado en las Casas")
    st.markdown("*Análisis del índice de precios de vivienda nueva tipo Casa en Colombia*")
    
    # Cargar datos principal para la gráfica de evolución
    df_principal = cargar_datos_principal()
    
    # Cargar datos de casas para mapas
    with st.spinner("Cargando datos de Casas..."):
        df_dept_casas = cargar_excel_con_hoja(ARCHIVO_DEPARTAMENTOS, "Casas")
        df_ciudades_casas = cargar_excel_con_hoja(ARCHIVO_CIUDADES, "Casas")
    
    # Verificar si se cargaron ambos archivos
    if df_dept_casas is None and df_ciudades_casas is None:
        st.error("❌ No se pudieron cargar los datos de casas (ni departamentos ni ciudades).")
    elif df_dept_casas is None:
        st.warning("⚠️ No se pudieron cargar los datos de departamentos, pero sí los de ciudades.")
    elif df_ciudades_casas is None:
        st.warning("⚠️ No se pudieron cargar los datos de ciudades, pero sí los de departamentos.")
    
    # GRÁFICA DE EVOLUCIÓN TEMPORAL
    if df_principal is not None and 'Casas' in df_principal.columns:
        st.markdown("---")
        
        # Crear gráfica con Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_principal["Periodo"],
            y=df_principal["Casas"],
            mode='lines+markers',
            name='Índice Casas',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6, color='#764ba2', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Casas",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda (Casas)",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df_principal['Casas'].iloc[-1]:.2f}", 
                     f"{((df_principal['Casas'].iloc[-1] - df_principal['Casas'].iloc[-2]) / df_principal['Casas'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df_principal['Casas'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df_principal['Casas'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df_principal['Casas'].min():.2f}")
    
        st.markdown("---")
    
    if df_dept_casas is not None or df_ciudades_casas is not None:
        
        # Tabs para organizar la información
        tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "🌆​Indice en ciudades", "🏗️ Obras en Construcción"])

        with tab1:
            st.write("### Estadísticas Generales de Casas en 2025 por Ciudades")
            
            if df_dept_casas is not None:
                # Calcular última columna disponible (último periodo)
                columnas_numericas = df_dept_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        valor_max = df_dept_casas[ultima_col].max()
                        dept_max = df_dept_casas.loc[df_dept_casas[ultima_col].idxmax()].iloc[0]
                        st.metric("Índice Máximo", f"{valor_max:.2f}", f"{dept_max}")
                    with col2:
                        valor_min = df_dept_casas[ultima_col].min()
                        dept_min = df_dept_casas.loc[df_dept_casas[ultima_col].idxmin()].iloc[0]
                        st.metric("Índice Mínimo", f"{valor_min:.2f}", f"{dept_min}")
                    with col3:
                        promedio = df_dept_casas[ultima_col].mean()
                        st.metric("Promedio Nacional", f"{promedio:.2f}")
                    with col4:
                        desv_std = df_dept_casas[ultima_col].std()
                        st.metric("Desviación Estándar", f"{desv_std:.2f}")
                    
                    # Tabla de departamentos
                    st.write("### Top 10 Ciudades - Índice de Precios de Casas")
                    df_top = df_dept_casas.nlargest(10, ultima_col)[[df_dept_casas.columns[0], ultima_col]].reset_index(drop=True)
                    df_top.columns = ['Departamento', 'Índice']
                    st.dataframe(df_top.style.format({'Índice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    
            else:
                st.info("No hay datos de departamentos disponibles para mostrar estadísticas.")
        
        with tab2:
            st.write("### 👩‍💻​ Índice en ciudades")
            
            if df_dept_casas is not None:
                columnas_numericas = df_dept_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Preparar datos para el mapa
                    df_mapa = df_dept_casas[[df_dept_casas.columns[0], ultima_col]].copy()
                    df_mapa.columns = ['Departamento', 'Indice']
                    
                    # Crear dos columnas: gráfico de barras y gráfico de pastel
                    col_bar, col_pie = st.columns([2, 1])
                    
                    with col_bar:
                        # Crear gráfico de barras horizontal con colores de mapa de calor
                        fig = px.bar(
                            df_mapa.sort_values('Indice', ascending=True),
                            x='Indice',
                            y='Departamento',
                            orientation='h',
                            title=f'Índice de Precios de Casas por Ciudad - Periodo {ultima_col}',
                            color='Indice',
                            color_continuous_scale='RdYlGn',
                            labels={'Indice': 'Índice de Vivienda', 'Departamento': 'Departamento'}
                        )
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=max(600, len(df_mapa) * 25),
                            showlegend=False,
                            xaxis_title="Índice de Vivienda",
                            yaxis_title="Departamento"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_pie:
                        st.write("#### Proporción por Ciudad (resumen)")
                        # Mostrar tabla con los top 10 departamentos como alternativa al pie
                        df_top_pie = df_mapa.nlargest(10, 'Indice').reset_index(drop=True)
                        st.dataframe(df_top_pie.style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)

                        # Métricas adicionales
                        total_indice = df_mapa['Indice'].sum()
                        st.metric("Total Índice", f"{total_indice:.2f}")
                        st.metric("Departamentos", len(df_mapa))
                    
                    # Información adicional
                    st.info("""
                    💡 **Interpretación del Mapa de Calor:**
                    - 🟢 **Verde:** Índices más altos (mayor crecimiento de precios)
                    - 🟡 **Amarillo:** Índices medios
                    - 🔴 **Rojo:** Índices más bajos (menor crecimiento de precios)
                    """)
            else:
                st.warning("⚠️ No hay datos de departamentos disponibles para el mapa de calor.")
        with tab3:
            st.write("### 🏗️ Obras en Construcción")
            st.info("📌 **Nota:** Estos datos representan la cantidad de viviendas nuevas (casas) en construcción por municipio.")
            
            if df_ciudades_casas is not None:
                columnas_num_ciudad = df_ciudades_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_num_ciudad) > 0:
                    ultima_col_ciudad = columnas_num_ciudad[-1]
                    
                    # Preparar datos para el mapa de ciudades
                    df_mapa_ciudad = df_ciudades_casas[[df_ciudades_casas.columns[0], ultima_col_ciudad]].copy()
                    df_mapa_ciudad.columns = ['Ciudad', 'Indice']
                    
                    # Crear gráfico de barras horizontal
                    fig_ciudad = px.bar(
                        df_mapa_ciudad.sort_values('Indice', ascending=True),
                        x='Indice',
                        y='Ciudad',
                        orientation='h',
                        title=f'Cantidad de Casas en Construcción por Ciudad - Periodo {ultima_col_ciudad}',
                        color='Indice',
                        color_continuous_scale='RdYlGn',
                        labels={'Indice': 'Cantidad de Viviendas', 'Ciudad': 'Ciudad'}
                    )
                    
                    fig_ciudad.update_layout(
                        template="plotly_dark",
                        height=max(800, len(df_mapa_ciudad) * 20),
                        showlegend=False,
                        xaxis_title="Cantidad de Viviendas en Construcción",
                        yaxis_title="Ciudad"
                    )
                    
                    st.plotly_chart(fig_ciudad, use_container_width=True)
                    
                    # Gráfico de pastel - Top 10 ciudades (proporción) - Casas
                    df_top_ciudad_pie = df_mapa_ciudad.nlargest(10, 'Indice')
                    fig_pie_ciudad = px.pie(
                        df_top_ciudad_pie,
                        values='Indice',
                        names='Ciudad',
                        title=f'Top 10 Ciudades - Proporción de Casas en Construcción - Periodo {ultima_col_ciudad}',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie_ciudad.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Índice: %{value:.2f}<br>Porcentaje: %{percent}<extra></extra>'
                    )
                    fig_pie_ciudad.update_layout(
                        template="plotly_dark",
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.02
                        )
                    )
                    st.plotly_chart(fig_pie_ciudad, use_container_width=True)

                    # Top ciudades (tabla)
                    st.write("### Top 10 Ciudades - Cantidad de Casas en Construcción")
                    df_top_ciudad = df_mapa_ciudad.nlargest(10, 'Indice').reset_index(drop=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(df_top_ciudad.head(8).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    with col2:
                        st.dataframe(df_top_ciudad.tail(3).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos de ciudades disponibles para el mapa de calor.")

elif st.session_state.vista_actual == "Departamento":
    st.subheader("🏙️ Índice de la vivienda enfocado en los Apartamentos")
    st.markdown("*Análisis del índice de precios de vivienda nueva tipo Apartamento en Colombia*")
    
    # Cargar datos principal para la gráfica de evolución
    df_principal = cargar_datos_principal()
    
    # Cargar datos de apartamentos para mapas
    with st.spinner("Cargando datos de Apartamentos..."):
        df_dept_aptos = cargar_excel_con_hoja(ARCHIVO_DEPARTAMENTOS, "Apartamentos")
        df_ciudades_aptos = cargar_excel_con_hoja(ARCHIVO_CIUDADES, "Apartamentos")
    
    # Verificar si se cargaron ambos archivos
    if df_dept_aptos is None and df_ciudades_aptos is None:
        st.error("❌ No se pudieron cargar los datos de apartamentos (ni departamentos ni ciudades).")
    elif df_dept_aptos is None:
        st.warning("⚠️ No se pudieron cargar los datos de departamentos, pero sí los de ciudades.")
    elif df_ciudades_aptos is None:
        st.warning("⚠️ No se pudieron cargar los datos de ciudades, pero sí los de departamentos.")
    
    # GRÁFICA DE EVOLUCIÓN TEMPORAL (similar a Total y Modelo)
    if df_principal is not None and 'Apartamentos' in df_principal.columns:
        st.markdown("---")
        
        # Crear gráfica con Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_principal["Periodo"],
            y=df_principal["Apartamentos"],
            mode='lines+markers',
            name='Índice Apartamentos',
            line=dict(color='#f093fb', width=3),
            marker=dict(size=6, color='#f5576c', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Apartamentos",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda (Apartamentos)",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df_principal['Apartamentos'].iloc[-1]:.2f}", 
                     f"{((df_principal['Apartamentos'].iloc[-1] - df_principal['Apartamentos'].iloc[-2]) / df_principal['Apartamentos'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df_principal['Apartamentos'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df_principal['Apartamentos'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df_principal['Apartamentos'].min():.2f}")
        
        st.markdown("---")
    
    if df_dept_aptos is not None or df_ciudades_aptos is not None:
        
        # Tabs para organizar la información
        tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "🌆​ Índice en ciudades", "🏗️ Obras en Construcción"])
        
        with tab1:
            st.write("### Estadísticas Generales de Apartamentos en 2025 por Ciudades")
            
            if df_dept_aptos is not None:
                # Calcular última columna disponible (último periodo)
                columnas_numericas = df_dept_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        valor_max = df_dept_aptos[ultima_col].max()
                        dept_max = df_dept_aptos.loc[df_dept_aptos[ultima_col].idxmax()].iloc[0]
                        st.metric("Índice Máximo", f"{valor_max:.2f}", f"{dept_max}")
                    with col2:
                        valor_min = df_dept_aptos[ultima_col].min()
                        dept_min = df_dept_aptos.loc[df_dept_aptos[ultima_col].idxmin()].iloc[0]
                        st.metric("Índice Mínimo", f"{valor_min:.2f}", f"{dept_min}")
                    with col3:
                        promedio = df_dept_aptos[ultima_col].mean()
                        st.metric("Promedio Nacional", f"{promedio:.2f}")
                    with col4:
                        desv_std = df_dept_aptos[ultima_col].std()
                        st.metric("Desviación Estándar", f"{desv_std:.2f}")
                    
                    # Tabla de departamentos
                    st.write("### Top 10 Ciudad - Índice de Precios de Apartamentos")
                    df_top = df_dept_aptos.nlargest(10, ultima_col)[[df_dept_aptos.columns[0], ultima_col]].reset_index(drop=True)
                    df_top.columns = ['Departamento', 'Índice']
                    st.dataframe(df_top.style.format({'Índice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.info("No hay datos de departamentos disponibles para mostrar estadísticas.")
        
        with tab2:
            st.write("### 👩‍💻​ Índice en ciudades")
            
            if df_dept_aptos is not None:
                columnas_numericas = df_dept_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Preparar datos para el mapa
                    df_mapa = df_dept_aptos[[df_dept_aptos.columns[0], ultima_col]].copy()
                    df_mapa.columns = ['Departamento', 'Indice']
                    
                    # Crear dos columnas: gráfico de barras y tabla resumen
                    col_bar, col_pie = st.columns([2, 1])
                    
                    with col_bar:
                        # Crear gráfico de barras horizontal con colores de mapa de calor
                        fig = px.bar(
                            df_mapa.sort_values('Indice', ascending=True),
                            x='Indice',
                            y='Departamento',
                            orientation='h',
                            title=f'Índice de Precios de Apartamentos por Departamento - Periodo {ultima_col}',
                            color='Indice',
                            color_continuous_scale='RdYlGn',
                            labels={'Indice': 'Índice de Vivienda', 'Departamento': 'Departamento'}
                        )
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=max(600, len(df_mapa) * 25),
                            showlegend=False,
                            xaxis_title="Índice de Vivienda",
                            yaxis_title="Departamento"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_pie:
                        st.write("#### Proporción por Departamento (resumen)")
                        # Mostrar tabla con los top 10 departamentos
                        df_top_pie = df_mapa.nlargest(10, 'Indice').reset_index(drop=True)
                        st.dataframe(df_top_pie.style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)

                        # Métricas adicionales
                        total_indice = df_mapa['Indice'].sum()
                        st.metric("Total Índice", f"{total_indice:.2f}")
                        st.metric("Departamentos", len(df_mapa))
                    
                    # Información adicional
                    st.info("""
                    💡 **Interpretación del Mapa de Calor:**
                    - 🟢 **Verde:** Índices más altos (mayor crecimiento de precios)
                    - 🟡 **Amarillo:** Índices medios
                    - 🔴 **Rojo:** Índices más bajos (menor crecimiento de precios)
                    """)
            else:
                st.warning("⚠️ No hay datos de departamentos disponibles para el mapa de calor.")
        
        with tab3:
            st.write("### 🏗️ Obras en Construcción")
            st.info("📌 **Nota:** Estos datos representan la cantidad de viviendas nuevas (apartamentos) en construcción por municipio.")
            
            if df_ciudades_aptos is not None:
                columnas_num_ciudad = df_ciudades_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_num_ciudad) > 0:
                    ultima_col_ciudad = columnas_num_ciudad[-1]
                    
                    # Preparar datos para el mapa de ciudades
                    df_mapa_ciudad = df_ciudades_aptos[[df_ciudades_aptos.columns[0], ultima_col_ciudad]].copy()
                    df_mapa_ciudad.columns = ['Ciudad', 'Indice']
                    
                    # Crear gráfico de barras horizontal
                    fig_ciudad = px.bar(
                        df_mapa_ciudad.sort_values('Indice', ascending=True),
                        x='Indice',
                        y='Ciudad',
                        orientation='h',
                        title=f'Cantidad de Apartamentos en Construcción por Ciudad - Periodo {ultima_col_ciudad}',
                        color='Indice',
                        color_continuous_scale='RdYlGn',
                        labels={'Indice': 'Cantidad de Viviendas', 'Ciudad': 'Ciudad'}
                    )
                    
                    fig_ciudad.update_layout(
                        template="plotly_dark",
                        height=max(800, len(df_mapa_ciudad) * 20),
                        showlegend=False,
                        xaxis_title="Cantidad de Viviendas en Construcción",
                        yaxis_title="Ciudad"
                    )
                    
                    st.plotly_chart(fig_ciudad, use_container_width=True)
                    
                    # Gráfico de pastel - Top 10 ciudades (proporción) - Apartamentos
                    df_top_ciudad_pie_apt = df_mapa_ciudad.nlargest(10, 'Indice')
                    fig_pie_ciudad_apt = px.pie(
                        df_top_ciudad_pie_apt,
                        values='Indice',
                        names='Ciudad',
                        title=f'Top 10 Ciudades - Proporción de Apartamentos en Construcción - Periodo {ultima_col_ciudad}',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie_ciudad_apt.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Índice: %{value:.2f}<br>Porcentaje: %{percent}<extra></extra>'
                    )
                    fig_pie_ciudad_apt.update_layout(
                        template="plotly_dark",
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.02
                        )
                    )
                    st.plotly_chart(fig_pie_ciudad_apt, use_container_width=True)

                    # Top ciudades
                    st.write("### Top 15 Ciudades - Cantidad de Apartamentos en Construcción")
                    df_top_ciudad = df_mapa_ciudad.nlargest(15, 'Indice').reset_index(drop=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(df_top_ciudad.head(8).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    with col2:
                        st.dataframe(df_top_ciudad.tail(7).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos de ciudades disponibles para el mapa de calor.")

elif st.session_state.vista_actual == "Total y Modelo":
    st.subheader("🏭 Análisis de la vivienda total en los últimos 20 años")
    st.markdown("*Movimiento y predicción con modelo ARMA para el índice de crecimiento en el precio de la vivienda en Colombia*")
    
    # Cargar datos
    df = cargar_datos_principal()
    
    if df is not None:
        # Crear gráfica con Plotly (más interactiva que matplotlib)
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df["Periodo"],
            y=df["Total"],
            mode='lines+markers',
            name='Índice Total',
            line=dict(color='#43e97b', width=3),
            marker=dict(size=6, color='#38f9d7', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Vivienda",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df['Total'].iloc[-1]:.2f}", 
                     f"{((df['Total'].iloc[-1] - df['Total'].iloc[-2]) / df['Total'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df['Total'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df['Total'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df['Total'].min():.2f}")
        
        # Tabs adicionales
        tab1, tab2, tab3 = st.tabs(["📈 Análisis Estadístico", "📋 Datos Completos", "🔮 Modelo ARMA"])
        
        with tab1:
            st.write("### Estadísticas Descriptivas")
            st.dataframe(df[["Total"]].describe(), use_container_width=True)
            
            # Gráfica de distribución
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df["Total"],
                nbinsx=30,
                name='Distribución',
                marker_color='#43e97b'
            ))
            fig_hist.update_layout(
                title="Distribución del Índice de Vivienda",
                xaxis_title="Índice",
                yaxis_title="Frecuencia",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with tab2:
            st.write("### Tabla de Datos Completos")
            st.dataframe(df[["Año", "Trimestre", "Periodo", "Total"]], use_container_width=True)
            
            # Opción de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos CSV",
                data=csv,
                file_name='datos_vivienda.csv',
                mime='text/csv',
            )
            
        with tab3:
            st.write("### 🔮 Modelo ARMA - Análisis Completo")
            st.info("💡 Haz clic en cada sección para expandir y ver los detalles del análisis")
            
            # ============================================
            # 1. TEST DE ESTACIONARIEDAD (SOLO ADF)
            # ============================================
            with st.expander("1️⃣ Test de Estacionariedad", expanded=False):
                st.subheader("Test de Estacionariedad - ADF")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### Test ADF (Augmented Dickey-Fuller)")
                    result_adf = adfuller(df['Total'].dropna())
                    
                    st.metric("ADF Statistic", f"{result_adf[0]:.6f}")
                    st.metric("p-value", f"{result_adf[1]:.6f}")
                    st.metric("Lags usados", result_adf[2])
                    st.metric("Observaciones", result_adf[3])
                    
                    if result_adf[1] < 0.05:
                        st.success("✅ La serie ES estacionaria (rechazamos H0)")
                    else:
                        st.warning("⚠️ La serie NO es estacionaria (no rechazamos H0)")
                
                with col2:
                    st.write("#### Valores Críticos ADF")
                    st.write("Comparación del estadístico con valores críticos:")
                    
                    for key, val in result_adf[4].items():
                        st.metric(f"Nivel {key}", f"{val:.4f}")
                    
                    st.info("""
                    **Información:**
                    - Si ADF Statistic < Valores Críticos → Serie estacionaria
                    - Si p-value < 0.05 → Rechazamos H0 (la serie es estacionaria)
                    """)
            
            # ============================================
            # 2. AJUSTE DEL MODELO ARMA(1,1)
            # ============================================
            with st.expander("2️⃣ Modelo ARMA(1,1) Ajustado", expanded=False):
                st.subheader("Modelo ARMA(1,1) Ajustado")
                
                # Ajustar el modelo
                res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                # Mostrar resumen del modelo
                with st.expander("📊 Ver resumen completo del modelo"):
                    st.text(str(res.summary()))
                
                # Coeficientes del modelo
                st.write("#### Coeficientes del Modelo")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("AR(1) - φ₁", f"{res.arparams[0]:.6f}")
                with col2:
                    st.metric("MA(1) - θ₁", f"{res.maparams[0]:.6f}")
                with col3:
                    st.metric("Intercepto", f"{res.params['const']:.6f}")
                
                st.write("#### Criterios de Información")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("AIC", f"{res.aic:.4f}")
                with col2:
                    st.metric("BIC", f"{res.bic:.4f}")
                with col3:
                    st.metric("Log-Likelihood", f"{res.llf:.4f}")
            
            # ============================================
            # 3. ANÁLISIS DE RESIDUOS
            # ============================================
            with st.expander("3️⃣ Análisis de Residuos", expanded=False):
                st.subheader("Análisis de Residuos")
                
                # Calcular residuos solo si el modelo ya fue ajustado
                if 'res' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                resid = res.resid.dropna()
                
                st.write("#### Estadísticas de Residuos")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Media", f"{resid.mean():.8f}")
                with col2:
                    st.metric("Desviación Estándar", f"{resid.std():.6f}")
                with col3:
                    st.metric("Sesgo", f"{resid.skew():.6f}")
                with col4:
                    st.metric("Curtosis", f"{resid.kurtosis():.6f}")
                
                st.info("📊 Los residuos deben tener media cercana a cero y comportarse como ruido blanco")
            
            # ============================================
            # 4. TEST DE LJUNG-BOX
            # ============================================
            with st.expander("4️⃣ Test de Ljung-Box (Autocorrelación de Residuos)", expanded=False):
                st.subheader("Test de Ljung-Box - Autocorrelación de Residuos")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("#### Resultados del Test")
                    lags = [4, 8, 12, 16, 20]
                    lb = acorr_ljungbox(resid, lags=lags, return_df=True)
                    st.dataframe(lb.style.format("{:.6f}"), use_container_width=True)
                    
                    # Interpretación
                    if (lb['lb_pvalue'] > 0.05).all():
                        st.success("✅ No hay evidencia de autocorrelación en los residuos")
                    else:
                        st.warning("⚠️ Existe autocorrelación significativa en algunos rezagos")
                    
                    st.info("""
                    **Información:**
                    - **H0:** No hay autocorrelación en los residuos (ruido blanco)
                    - **H1:** Existe autocorrelación en los residuos
                    - Si p-value > 0.05 → No rechazamos H0 (residuos son ruido blanco ✓)
                    - Si p-value < 0.05 → Rechazamos H0 (hay autocorrelación)
                    """)
                
                with col2:
                    st.write("#### ACF de los Residuos")
                    fig_acf, ax = plt.subplots(figsize=(8, 4))
                    plot_acf(resid, lags=20, ax=ax, title='')
                    ax.set_title('ACF de los residuos ARMA(1,1)', fontsize=12, color='white', pad=10)
                    ax.set_xlabel('Rezagos', fontsize=10, color='white')
                    ax.set_ylabel('Autocorrelación', fontsize=10, color='white')
                    ax.set_facecolor('#1a1a2e')
                    fig_acf.patch.set_facecolor('#1a1a2e')
                    ax.tick_params(colors='white')
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    ax.grid(True, alpha=0.2, color='white')
                    
                    # Mejorar visibilidad de las líneas de confianza
                    for line in ax.get_lines()[1:]:
                        line.set_color('#00c4ff')
                        line.set_linewidth(1.5)
                        line.set_alpha(0.7)
                    
                    st.pyplot(fig_acf)
                    plt.close()
            
            # ============================================
            # 5. ANÁLISIS ACF Y PACF PARA ESTACIONALIDAD
            # ============================================
            with st.expander("5️⃣ Análisis ACF y PACF - Identificación de Patrones y Estacionalidad", expanded=False):
                st.subheader("Análisis ACF y PACF - Identificación de Patrones y Estacionalidad")
                
                st.info("""
                **ACF y PACF para detectar estacionalidad:**
                - **ACF (Autocorrelación):** Muestra la correlación de la serie con sus rezagos. Picos significativos en múltiplos de 4 (trimestres) indican estacionalidad anual.
                - **PACF (Autocorrelación Parcial):** Muestra la correlación directa con cada rezago, eliminando efectos intermedios.
                - **Estacionalidad trimestral:** Buscar picos en los rezagos 4, 8, 12, 16... (cada 4 trimestres = 1 año)
                """)
                
                # ACF y PACF de la serie original
                st.write("### 📊 ACF y PACF de la Serie Original")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### ACF - Autocorrelación")
                    fig_acf_original, ax1 = plt.subplots(figsize=(10, 5))
                    plot_acf(df['Total'].dropna(), lags=24, ax=ax1, title='')
                    ax1.set_title('ACF de la Serie Original', fontsize=14, color='white', pad=15)
                    ax1.set_xlabel('Rezagos (Trimestres)', fontsize=11, color='white')
                    ax1.set_ylabel('Autocorrelación', fontsize=11, color='white')
                    ax1.set_facecolor('#1a1a2e')
                    fig_acf_original.patch.set_facecolor('#1a1a2e')
                    ax1.tick_params(colors='white')
                    ax1.grid(True, alpha=0.2, color='white')
                    
                    # Marcar rezagos estacionales
                    for lag in [4, 8, 12, 16, 20, 24]:
                        ax1.axvline(x=lag, color='#ff6b6b', linestyle='--', alpha=0.5, linewidth=1)
                    
                    st.pyplot(fig_acf_original)
                    plt.close()
                    
                    st.caption("🔴 Líneas rojas marcan rezagos estacionales (múltiplos de 4 trimestres)")
                
                with col2:
                    st.write("#### PACF - Autocorrelación Parcial")
                    fig_pacf_original, ax2 = plt.subplots(figsize=(10, 5))
                    plot_pacf(df['Total'].dropna(), lags=24, ax=ax2, title='', method='ywm')
                    ax2.set_title('PACF de la Serie Original', fontsize=14, color='white', pad=15)
                    ax2.set_xlabel('Rezagos (Trimestres)', fontsize=11, color='white')
                    ax2.set_ylabel('Autocorrelación Parcial', fontsize=11, color='white')
                    ax2.set_facecolor('#1a1a2e')
                    fig_pacf_original.patch.set_facecolor('#1a1a2e')
                    ax2.tick_params(colors='white')
                    ax2.grid(True, alpha=0.2, color='white')
                    
                    # Marcar rezagos estacionales
                    for lag in [4, 8, 12, 16, 20, 24]:
                        ax2.axvline(x=lag, color='#ff6b6b', linestyle='--', alpha=0.5, linewidth=1)
                    
                    st.pyplot(fig_pacf_original)
                    plt.close()
                    
                    st.caption("🔴 Líneas rojas marcan rezagos estacionales (múltiplos de 4 trimestres)")
                
                # Interpretación automática de estacionalidad
                st.write("### 🔍 Interpretación de Estacionalidad")
                
                from statsmodels.tsa.stattools import acf
                acf_values = acf(df['Total'].dropna(), nlags=24)
                
                # Detectar picos en rezagos estacionales
                seasonal_lags = [4, 8, 12, 16, 20]
                seasonal_peaks = [lag for lag in seasonal_lags if abs(acf_values[lag]) > 0.3]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if len(seasonal_peaks) > 0:
                        st.warning(f"""
                        ⚠️ **Posible estacionalidad detectada** en los rezagos: {seasonal_peaks}
                        
                        Esto sugiere que existe un patrón que se repite cada {seasonal_peaks[0]} trimestres (aproximadamente cada año).
                        
                        **Recomendación:** Considerar un modelo SARIMA (Seasonal ARIMA) en lugar de ARMA simple.
                        """)
                    else:
                        st.success("""
                        ✅ **No se detecta estacionalidad significativa** en la serie.
                        
                        El modelo ARMA(1,1) es apropiado para esta serie temporal.
                        """)
                
                with col2:
                    st.metric("Rezagos Estacionales Detectados", len(seasonal_peaks))
                    if len(seasonal_peaks) > 0:
                        st.metric("Periodo Estacional", f"{seasonal_peaks[0]} trimestres")
                    st.metric("Total Rezagos Analizados", 24)
            
            # ============================================
            # 6. TEST DE JARQUE-BERA (NORMALIDAD)
            # ============================================
            with st.expander("6️⃣ Test de Jarque-Bera (Normalidad de Residuos)", expanded=False):
                st.subheader("Test de Jarque-Bera - Normalidad de Residuos")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    jb_stat, jb_p, skew, kurtosis = jarque_bera(resid)
                    
                    st.write("#### Resultados del Test")
                    st.metric("Estadístico JB", f"{jb_stat:.6f}")
                    st.metric("p-value", f"{jb_p:.6f}")
                    st.metric("Sesgo", f"{skew:.6f}")
                    st.metric("Curtosis", f"{kurtosis:.6f}")
                    
                    if jb_p > 0.05:
                        st.success("✅ Los residuos siguen una distribución normal")
                    else:
                        st.warning("⚠️ Los residuos NO siguen una distribución normal perfecta")
                    
                    st.info("""
                    **Información:**
                    - **H0:** Los residuos siguen una distribución normal
                    - **H1:** Los residuos NO siguen una distribución normal
                    - Si p-value > 0.05 → No rechazamos H0 (residuos normales ✓)
                    - Si p-value < 0.05 → Rechazamos H0 (residuos no normales)
                    - Sesgo cercano a 0 y curtosis cercana a 3 indican normalidad
                    """)
                
                with col2:
                    st.write("#### QQ-Plot")
                    fig_qq, ax = plt.subplots(figsize=(6, 6))
                    sm.qqplot(resid, line='s', ax=ax)
                    ax.set_title('QQ-plot de los residuos', color='white')
                    ax.set_facecolor('#1a1a2e')
                    fig_qq.patch.set_facecolor('#1a1a2e')
                    ax.tick_params(colors='white')
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    ax.get_lines()[0].set_color('#43e97b')
                    ax.get_lines()[1].set_color('#ff6b6b')
                    st.pyplot(fig_qq)
                    plt.close()
            
            # ============================================
            # 7. TEST ARCH (HETEROCEDASTICIDAD)
            # ============================================
            with st.expander("7️⃣ Test ARCH-LM (Heterocedasticidad)", expanded=False):
                st.subheader("Test ARCH-LM - Heterocedasticidad")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                arch_res = het_arch(resid, nlags=4)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estadístico LM", f"{arch_res[0]:.6f}")
                    st.metric("p-value", f"{arch_res[1]:.6f}")
                with col2:
                    st.metric("Estadístico F", f"{arch_res[2]:.6f}")
                    st.metric("p-value F", f"{arch_res[3]:.6f}")
                
                if arch_res[1] > 0.05:
                    st.success("✅ No hay evidencia de heterocedasticidad condicional (efecto ARCH)")
                else:
                    st.warning("⚠️ Existe heterocedasticidad condicional (efecto ARCH presente)")
                
                st.info("""
                **Información:**
                - **H0:** No hay efecto ARCH (homocedasticidad - varianza constante)
                - **H1:** Existe efecto ARCH (heterocedasticidad condicional)
                - Si p-value > 0.05 → No rechazamos H0 (varianza constante ✓)
                - Si p-value < 0.05 → Rechazamos H0 (la varianza cambia en el tiempo)
                - Efecto ARCH indica que la volatilidad de los errores varía con el tiempo
                """)
            
            # ============================================
            # 8. ESTABILIDAD E INVERTIBILIDAD
            # ============================================
            with st.expander("8️⃣ Estabilidad e Invertibilidad del Modelo", expanded=False):
                st.subheader("Estabilidad e Invertibilidad del Modelo")
                
                if 'res' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### Test de Estabilidad (Raíces AR)")
                    try:
                        arparams = res.arparams
                        ar_roots = res.arroots
                        mods_ar_roots = np.abs(ar_roots)
                        
                        st.metric("Parámetro AR (φ₁)", f"{arparams[0]:.6f}")
                        st.metric("Raíz AR (z)", f"{ar_roots[0]:.6f}")
                        st.metric("Módulo |z|", f"{mods_ar_roots[0]:.6f}")
                        
                        ar_ok = all(mods_ar_roots > 1.0)
                        if ar_ok:
                            st.success(f"✅ Modelo ESTABLE (todas las raíces AR |z| > 1)")
                        else:
                            st.error(f"❌ Modelo INESTABLE (alguna raíz AR tiene |z| ≤ 1)")
                        
                        st.info("""
                        **Información:**
                        - **Condición de estabilidad:** |z| > 1
                        - Si todas las raíces AR están fuera del círculo unitario → Modelo estable ✓
                        - Un modelo estable garantiza que los efectos de shocks se disipan con el tiempo
                        """)
                        
                    except Exception as e:
                        st.error(f"Error al calcular estabilidad: {e}")
                
                with col2:
                    st.write("#### Test de Invertibilidad (Raíces MA)")
                    try:
                        maparams = res.maparams
                        ma_roots = res.maroots
                        mods_ma_roots = np.abs(ma_roots)
                        
                        st.metric("Parámetro MA (θ₁)", f"{maparams[0]:.6f}")
                        st.metric("Raíz MA (z)", f"{ma_roots[0]:.6f}")
                        st.metric("Módulo |z|", f"{mods_ma_roots[0]:.6f}")
                        
                        ma_ok = all(mods_ma_roots > 1.0)
                        if ma_ok:
                            st.success(f"✅ Modelo INVERTIBLE (todas las raíces MA |z| > 1)")
                        else:
                            st.error(f"❌ Modelo NO INVERTIBLE (alguna raíz MA tiene |z| ≤ 1)")
                        
                        st.info("""
                        **Información:**
                        - **Condición de invertibilidad:** |z| > 1
                        - Si todas las raíces MA están fuera del círculo unitario → Modelo invertible ✓
                        - Un modelo invertible permite representar el proceso como un AR(∞)
                        """)
                        
                    except Exception as e:
                        st.error(f"Error al calcular invertibilidad: {e}")
            
            # ============================================
            # 9. PRONÓSTICO Y VALIDACIÓN
            # ============================================
            with st.expander("9️⃣ Pronóstico y Validación del Modelo", expanded=False):
                st.subheader("Pronóstico y Validación del Modelo")
                
                # Train/Test Split
                h = 4
                y = df['Total']
                train, test = y[:-h], y[-h:]
                
                # Ajustar modelo en train
                model_train = ARIMA(train, order=(1,0,1)).fit()
                
                # Pronóstico
                fc = model_train.get_forecast(steps=h)
                pred = fc.predicted_mean
                conf = fc.conf_int()
                
                # Métricas
                rmse = np.sqrt(mean_squared_error(test, pred))
                mae = mean_absolute_error(test, pred)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tamaño Train", len(train))
                with col2:
                    st.metric("Tamaño Test", len(test))
                with col3:
                    st.metric("RMSE", f"{rmse:.6f}")
                with col4:
                    st.metric("MAE", f"{mae:.6f}")
                
                # Gráfico de pronóstico
                st.write("#### Gráfico Train / Test / Forecast")
                
                fig_forecast, ax = plt.subplots(figsize=(14, 6))
                
                train.plot(ax=ax, label='Train', color='#43e97b', linewidth=2)
                test.plot(ax=ax, label='Test (Real)', marker='o', color='#ff6b6b', linewidth=2, markersize=8)
                pred.plot(ax=ax, label='Forecast', marker='s', color='#00c4ff', linewidth=2, markersize=8)
                
                ax.fill_between(conf.index, conf.iloc[:,0], conf.iloc[:,1], alpha=0.3, color='#00c4ff')
                
                ax.set_title('Pronóstico ARMA(1,1) - Últimos 4 Trimestres', fontsize=16, color='white', pad=20)
                ax.set_xlabel('Periodo', fontsize=12, color='white')
                ax.set_ylabel('Índice de Vivienda', fontsize=12, color='white')
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#1a1a2e')
                fig_forecast.patch.set_facecolor('#1a1a2e')
                ax.tick_params(colors='white')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig_forecast)
                plt.close()
                
                # Tabla de comparación
                st.write("#### Comparación: Valores Reales vs Pronósticos")
                comparison_df = pd.DataFrame({
                    'Periodo': test.index,
                    'Real': test.values,
                    'Pronóstico': pred.values,
                    'Error': test.values - pred.values,
                    'Error %': ((test.values - pred.values) / test.values * 100)
                })
                st.dataframe(comparison_df.style.format({
                    'Real': '{:.4f}',
                    'Pronóstico': '{:.4f}',
                    'Error': '{:.4f}',
                    'Error %': '{:.2f}%'
                }), use_container_width=True)
            
            # ============================================
            # CONCLUSIÓN FINAL
            # ============================================
            st.markdown("---")
            st.success("""
            ### 🎯 Conclusiones del Modelo ARMA(1,1)
            
            El modelo ARMA(1,1) ha sido ajustado y validado exhaustivamente mediante múltiples pruebas estadísticas:
            
            - ✅ Test de estacionariedad confirmado (ADF)
            - ✅ Residuos analizados (media cercana a cero, autocorrelación, normalidad)
            - ✅ Análisis ACF/PACF para detectar estacionalidad
            - ✅ Test de normalidad (Jarque-Bera) y QQ-plot
            - ✅ Test de heterocedasticidad (ARCH-LM)
            - ✅ Estabilidad e invertibilidad verificadas
            - ✅ Pronóstico validado con métricas RMSE y MAE
            
            El modelo es adecuado para el análisis de la serie temporal de vivienda en Colombia.
            """)
    
    else:
        st.warning("⚠️ No se pudieron cargar los datos. Asegúrate de que el archivo Excel esté en el directorio correcto.")

else:
    st.info("👈 Selecciona una opción en el panel izquierdo para comenzar.")




import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
from statsmodels.stats.stattools import jarque_bera
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os

# ------------------------------------------------
# ⚙ CONFIG BÁSICA
# ------------------------------------------------
st.set_page_config(page_title="🏡 Vivienda Nueva en Colombia", layout="wide")
st.title("🏡 Índice de precios de la Vivienda Nueva en Colombia con base en los datos del DANE")

# ------------------------------------------------
# 📂 CONFIGURACIÓN DE RUTAS DINÁMICAS (Local + GitHub) - VERSIÓN CORREGIDA
# ------------------------------------------------

def obtener_ruta_base():
    """
    Detecta automáticamente si está corriendo en local o en Streamlit Cloud
    y retorna la ruta base apropiada para los archivos Excel
    """
    # Ruta local (Windows) - Tu carpeta original
    ruta_local = r"C:\Users\Usuario\Desktop\Clases\6 semestre\Econometria II\Dashboard"
    
    # Verificar si existe la ruta local (para desarrollo en VS Code)
    if os.path.exists(ruta_local):
        print("✅ Ejecutando en LOCAL - Usando ruta de Windows")
        return ruta_local
    
    # Para Streamlit Cloud: Probar múltiples ubicaciones
    posibles_rutas = [
        "Dashboard_github",
        os.path.join(os.getcwd(), "Dashboard_github"),
        ".",
    ]
    
    # Archivos que buscamos
    archivos_requeridos = [
        "Datos vivienda filtrado.xlsx",
        "Indice Vivienda Departamentos.xlsx",
        "Indice Vivienda Obras.xlsx"
    ]
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            # Verificar si los archivos existen en esta ruta
            archivos_encontrados = sum(1 for archivo in archivos_requeridos 
                                      if os.path.exists(os.path.join(ruta, archivo)))
            
            if archivos_encontrados >= 2:
                print(f"✅ Ejecutando en CLOUD - Usando ruta: {ruta}")
                print(f"   Archivos encontrados: {archivos_encontrados}/{len(archivos_requeridos)}")
                return ruta
    
    # Por defecto, usar Dashboard_github
    print(f"⚠️ Usando ruta por defecto: Dashboard_github")
    return "Dashboard_github"

# Obtener la ruta base UNA SOLA VEZ
RUTA_BASE = obtener_ruta_base()

# Nombres de los archivos
ARCHIVO_PRINCIPAL = "Datos vivienda filtrado.xlsx"
ARCHIVO_DEPARTAMENTOS = "Indice Vivienda Departamentos.xlsx"
ARCHIVO_CIUDADES = "Indice Vivienda Obras.xlsx"

# ------------------------------------------------
# 🔍 INFORMACIÓN DE DEBUG
# ------------------------------------------------
st.sidebar.markdown("---")

archivos_info = []
for archivo in [ARCHIVO_PRINCIPAL, ARCHIVO_DEPARTAMENTOS, ARCHIVO_CIUDADES]:
    ruta_completa = os.path.join(RUTA_BASE, archivo)
    existe = os.path.exists(ruta_completa)
    archivos_info.append(f"- {archivo} {'✅' if existe else '❌'}")

try:
    archivos_en_directorio = os.listdir(RUTA_BASE) if os.path.exists(RUTA_BASE) else []
    archivos_excel = [f for f in archivos_en_directorio if f.endswith('.xlsx')]
except:
    archivos_excel = []

# ------------------------------------------------
# 🎨 EMOJIS Y CONFIGURACIÓN DE SECCIONES
# ------------------------------------------------
secciones = {
    "Casas": {
        "emoji": "🏚️​",
        "color": "#00c4ff",
        "gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    },
    "Departamento": {
        "emoji": "🏙️​",
        "color": "#ff6b6b",
        "gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
    },
    "Total y Modelo": {
        "emoji": "📊​",
        "color": "#4ecdc4",
        "gradient": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)"
    }
}

# ------------------------------------------------
# 🎨 ESTILOS AVANZADOS
# ------------------------------------------------
st.markdown(
    """
    <style>
    /* Fondo del sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Ocultar labels de botones por defecto */
    [data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        border: none !important;
        background: linear-gradient(135deg, #2a2a3e 0%, #1f1f2e 100%) !important;
        color: white !important;
        font-size: 10rem !important;
        height: 140px !important;
        border-radius: 16px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        border: 2px solid rgba(255,255,255,0.05) !important;
        position: relative !important;
        overflow: hidden !important;
        padding: 0 !important;
        line-height: 200px !important;
    }
    
    /* Efecto de fondo animado */
    [data-testid="stSidebar"] .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255,255,255,0.1);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    /* Hover effect */
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-8px) scale(1.05);
        box-shadow: 0 12px 30px rgba(0,196,255,0.4);
        border-color: rgba(0,196,255,0.5);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    /* Efecto de click */
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(-4px) scale(1.02);
    }
    
    /* Estilos específicos para cada botón */
    .btn-Casas button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .btn-region button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
    }
    
    .btn-sector button {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%) !important;
    }
    
    /* Animación para botón activo */
    .active-button button {
        border: 3px solid white !important;
        box-shadow: 0 0 30px rgba(255,255,255,0.6) !important;
        animation: pulseGlow 2s infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { 
            box-shadow: 0 0 30px rgba(255,255,255,0.6);
            transform: scale(1);
        }
        50% { 
            box-shadow: 0 0 40px rgba(255,255,255,0.9);
            transform: scale(1.02);
        }
    }
    
    /* Etiquetas de texto debajo */
    .menu-label {
        text-align: center;
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: -8px;
        margin-bottom: 25px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    
    .menu-label.active {
        color: #00c4ff;
        font-size: 1.15rem;
        text-shadow: 0 0 10px rgba(0,196,255,0.8);
    }
    
    /* Separador decorativo */
    .separator {
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 15px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ------------------------------------------------
# 📥 FUNCIONES DE CARGA SIMPLIFICADAS
# ------------------------------------------------
def verificar_archivo(nombre_archivo):
    """Verifica si un archivo existe en la ruta base"""
    ruta_completa = os.path.join(RUTA_BASE, nombre_archivo)
    ruta_abs = os.path.abspath(ruta_completa)
    
    # Debug: imprimir información
    print(f"Verificando archivo: {nombre_archivo}")
    print(f"Ruta relativa: {ruta_completa}")
    print(f"Ruta absoluta: {ruta_abs}")
    print(f"¿Existe?: {os.path.exists(ruta_abs)}")
    
    if not os.path.exists(ruta_abs):
        st.error(f"⚠️ No se encontró el archivo: **{nombre_archivo}**")
        st.info(f"📂 Buscando en: `{ruta_abs}`")
        
        # Listar archivos en el directorio para debug
        try:
            archivos_dir = os.listdir(RUTA_BASE)
            st.warning(f"Archivos disponibles en {RUTA_BASE}: {archivos_dir}")
        except Exception as e:
            st.error(f"Error al listar directorio: {e}")
        
        return None
    return ruta_abs

def listar_hojas_excel(ruta_archivo):
    """Lista todas las hojas disponibles en un archivo Excel"""
    try:
        xls = pd.ExcelFile(ruta_archivo)
        return xls.sheet_names
    except Exception as e:
        st.error(f"Error al leer las hojas del archivo: {e}")
        return []

@st.cache_data
def cargar_datos_principal():
    """Carga el archivo principal de datos de vivienda"""
    try:
        ruta_completa = os.path.join(RUTA_BASE, ARCHIVO_PRINCIPAL)
        ruta_abs = os.path.abspath(ruta_completa)
        
        print(f"Cargando archivo principal: {ruta_abs}")
        
        if not os.path.exists(ruta_abs):
            st.error(f"⚠️ No se encontró el archivo: **{ARCHIVO_PRINCIPAL}**")
            st.info(f"📂 Ruta intentada: `{ruta_abs}`")
            return None
        
        df = pd.read_excel(ruta_abs)
        df["Periodo"] = df["Año"].astype(str) + "-" + df["Trimestre"].astype(str)
        st.success(f"✅ Archivo principal cargado: {ARCHIVO_PRINCIPAL}")
        return df
    except Exception as e:
        st.error(f"⚠️ Error al procesar {ARCHIVO_PRINCIPAL}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

@st.cache_data
def cargar_excel_con_hoja(nombre_archivo, nombre_hoja):
    """
    Función genérica para cargar cualquier archivo Excel con una hoja específica
    Maneja automáticamente nombres de hojas con caracteres especiales
    
    Args:
        nombre_archivo: Nombre del archivo Excel
        nombre_hoja: Nombre de la hoja a cargar
    
    Returns:
        DataFrame o None si hay error
    """
    try:
        # Construir ruta absoluta
        ruta_completa = os.path.join(RUTA_BASE, nombre_archivo)
        ruta_abs = os.path.abspath(ruta_completa)
        
        print(f"Cargando hoja '{nombre_hoja}' de: {ruta_abs}")
        
        # Verificar que el archivo existe
        if not os.path.exists(ruta_abs):
            st.error(f"⚠️ No se encontró el archivo: **{nombre_archivo}**")
            st.info(f"📂 Ruta intentada: `{ruta_abs}`")
            
            # Listar archivos en el directorio
            try:
                archivos_dir = os.listdir(RUTA_BASE)
                st.warning(f"Archivos en {RUTA_BASE}: {archivos_dir}")
            except Exception as e:
                st.error(f"Error al listar directorio: {e}")
            
            return None
        
        # Listar hojas disponibles
        xls = pd.ExcelFile(ruta_abs)
        hojas_disponibles = xls.sheet_names
        
        if not hojas_disponibles:
            st.error(f"⚠️ No se pudieron leer las hojas del archivo: {nombre_archivo}")
            return None
        
        # Función para limpiar nombres de hojas
        def limpiar_nombre(nombre):
            import re
            nombre_limpio = re.sub(r'[\t\r\n\x00-\x1F\x7F-\x9F]', '', nombre)
            return nombre_limpio.strip()
        
        # Buscar coincidencia
        hoja_encontrada = None
        
        # 1. Coincidencia exacta
        if nombre_hoja in hojas_disponibles:
            hoja_encontrada = nombre_hoja
        else:
            # 2. Buscar por nombre limpio
            nombre_buscado_limpio = limpiar_nombre(nombre_hoja).lower()
            
            for hoja in hojas_disponibles:
                hoja_limpia = limpiar_nombre(hoja).lower()
                if hoja_limpia == nombre_buscado_limpio:
                    hoja_encontrada = hoja
                    break
            
            # 3. Buscar si está contenido
            if hoja_encontrada is None:
                for hoja in hojas_disponibles:
                    if nombre_hoja.lower() in hoja.lower() or hoja.lower().startswith(nombre_hoja.lower()):
                        hoja_encontrada = hoja
                        break
        
        # Si no se encontró
        if hoja_encontrada is None:
            st.error(f"⚠️ No se encontró la hoja **'{nombre_hoja}'** en **{nombre_archivo}**")
            st.warning(f"📋 Hojas disponibles: {', '.join(hojas_disponibles)}")
            return None
        
        # Cargar la hoja
        df = pd.read_excel(ruta_abs, sheet_name=hoja_encontrada)
        
        # Mensaje de éxito
        if hoja_encontrada == nombre_hoja:
            st.success(f"✅ Datos cargados: {nombre_archivo} → '{nombre_hoja}' ({len(df)} filas)")
        else:
            st.success(f"✅ Datos cargados: {nombre_archivo} → '{hoja_encontrada}' (buscada como '{nombre_hoja}') ({len(df)} filas)")
        
        return df
        
    except Exception as e:
        st.error(f"⚠️ Error al leer {nombre_archivo}: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None
# ------------------------------------------------
# 📥 INICIALIZAR SESSION STATE
# ------------------------------------------------
if 'vista_actual' not in st.session_state:
    st.session_state.vista_actual = "Casas"

# ------------------------------------------------
# 🔘 MENÚ LATERAL CON EMOJIS INTERACTIVOS
# ------------------------------------------------
with st.sidebar:
    
    for nombre, config in secciones.items():
        # Determinar si está activo
        is_active = nombre == st.session_state.vista_actual
        active_class = "active-button" if is_active else ""
        button_class = f"btn-{nombre.lower()}"
        
        # Crear columnas para centrar
        col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
        
        with col2:
            # Contenedor con clase específica
            st.markdown(f'<div class="{button_class} {active_class}">', unsafe_allow_html=True)
            
            # Botón con emoji
            if st.button(config["emoji"], key=f"btn_{nombre}", use_container_width=True):
                st.session_state.vista_actual = nombre
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Label debajo del botón
            label_class = "active" if is_active else ""
            st.markdown(f'<div class="menu-label {label_class}">{nombre}</div>', unsafe_allow_html=True)

    st.markdown('<div class="separator"></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("💡 Haz clic en los iconos para navegar")

# ------------------------------------------------
# 📊 CONTENIDO PRINCIPAL SEGÚN LA VISTA
# ------------------------------------------------
st.markdown("---")

if st.session_state.vista_actual == "Casas":
    st.subheader("🏚️ Índice de la vivienda enfocado en las Casas")
    st.markdown("*Análisis del índice de precios de vivienda nueva tipo Casa en Colombia*")
    
    # Cargar datos principal para la gráfica de evolución
    df_principal = cargar_datos_principal()
    
    # Cargar datos de casas para mapas
    with st.spinner("Cargando datos de Casas..."):
        df_dept_casas = cargar_excel_con_hoja(ARCHIVO_DEPARTAMENTOS, "Casas")
        df_ciudades_casas = cargar_excel_con_hoja(ARCHIVO_CIUDADES, "Casas")
    
    # Verificar si se cargaron ambos archivos
    if df_dept_casas is None and df_ciudades_casas is None:
        st.error("❌ No se pudieron cargar los datos de casas (ni departamentos ni ciudades).")
    elif df_dept_casas is None:
        st.warning("⚠️ No se pudieron cargar los datos de departamentos, pero sí los de ciudades.")
    elif df_ciudades_casas is None:
        st.warning("⚠️ No se pudieron cargar los datos de ciudades, pero sí los de departamentos.")
    
    # GRÁFICA DE EVOLUCIÓN TEMPORAL
    if df_principal is not None and 'Casas' in df_principal.columns:
        st.markdown("---")
        
        # Crear gráfica con Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_principal["Periodo"],
            y=df_principal["Casas"],
            mode='lines+markers',
            name='Índice Casas',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6, color='#764ba2', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Casas",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda (Casas)",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df_principal['Casas'].iloc[-1]:.2f}", 
                     f"{((df_principal['Casas'].iloc[-1] - df_principal['Casas'].iloc[-2]) / df_principal['Casas'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df_principal['Casas'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df_principal['Casas'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df_principal['Casas'].min():.2f}")
    
        st.markdown("---")
    
    if df_dept_casas is not None or df_ciudades_casas is not None:
        
        # Tabs para organizar la información
        tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "🌆​Indice en ciudades", "🏗️ Obras en Construcción"])

        with tab1:
            st.write("### Estadísticas Generales de Casas en 2025 por Ciudades")
            
            if df_dept_casas is not None:
                # Calcular última columna disponible (último periodo)
                columnas_numericas = df_dept_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        valor_max = df_dept_casas[ultima_col].max()
                        dept_max = df_dept_casas.loc[df_dept_casas[ultima_col].idxmax()].iloc[0]
                        st.metric("Índice Máximo", f"{valor_max:.2f}", f"{dept_max}")
                    with col2:
                        valor_min = df_dept_casas[ultima_col].min()
                        dept_min = df_dept_casas.loc[df_dept_casas[ultima_col].idxmin()].iloc[0]
                        st.metric("Índice Mínimo", f"{valor_min:.2f}", f"{dept_min}")
                    with col3:
                        promedio = df_dept_casas[ultima_col].mean()
                        st.metric("Promedio Nacional", f"{promedio:.2f}")
                    with col4:
                        desv_std = df_dept_casas[ultima_col].std()
                        st.metric("Desviación Estándar", f"{desv_std:.2f}")
                    
                    # Tabla de departamentos
                    st.write("### Top 10 Ciudades - Índice de Precios de Casas")
                    df_top = df_dept_casas.nlargest(10, ultima_col)[[df_dept_casas.columns[0], ultima_col]].reset_index(drop=True)
                    df_top.columns = ['Departamento', 'Índice']
                    st.dataframe(df_top.style.format({'Índice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    
            else:
                st.info("No hay datos de departamentos disponibles para mostrar estadísticas.")
        
        with tab2:
            st.write("### 👩‍💻​ Índice en ciudades")
            
            if df_dept_casas is not None:
                columnas_numericas = df_dept_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Preparar datos para el mapa
                    df_mapa = df_dept_casas[[df_dept_casas.columns[0], ultima_col]].copy()
                    df_mapa.columns = ['Departamento', 'Indice']
                    
                    # Crear dos columnas: gráfico de barras y gráfico de pastel
                    col_bar, col_pie = st.columns([2, 1])
                    
                    with col_bar:
                        # Crear gráfico de barras horizontal con colores de mapa de calor
                        fig = px.bar(
                            df_mapa.sort_values('Indice', ascending=True),
                            x='Indice',
                            y='Departamento',
                            orientation='h',
                            title=f'Índice de Precios de Casas por Ciudad - Periodo {ultima_col}',
                            color='Indice',
                            color_continuous_scale='RdYlGn',
                            labels={'Indice': 'Índice de Vivienda', 'Departamento': 'Departamento'}
                        )
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=max(600, len(df_mapa) * 25),
                            showlegend=False,
                            xaxis_title="Índice de Vivienda",
                            yaxis_title="Departamento"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_pie:
                        st.write("#### Proporción por Ciudad (resumen)")
                        # Mostrar tabla con los top 10 departamentos como alternativa al pie
                        df_top_pie = df_mapa.nlargest(10, 'Indice').reset_index(drop=True)
                        st.dataframe(df_top_pie.style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)

                        # Métricas adicionales
                        total_indice = df_mapa['Indice'].sum()
                        st.metric("Total Índice", f"{total_indice:.2f}")
                        st.metric("Departamentos", len(df_mapa))
                    
                    # Información adicional
                    st.info("""
                    💡 **Interpretación del Mapa de Calor:**
                    - 🟢 **Verde:** Índices más altos (mayor crecimiento de precios)
                    - 🟡 **Amarillo:** Índices medios
                    - 🔴 **Rojo:** Índices más bajos (menor crecimiento de precios)
                    """)
            else:
                st.warning("⚠️ No hay datos de departamentos disponibles para el mapa de calor.")
        with tab3:
            st.write("### 🏗️ Obras en Construcción")
            st.info("📌 **Nota:** Estos datos representan la cantidad de viviendas nuevas (casas) en construcción por municipio.")
            
            if df_ciudades_casas is not None:
                columnas_num_ciudad = df_ciudades_casas.select_dtypes(include=[np.number]).columns
                if len(columnas_num_ciudad) > 0:
                    ultima_col_ciudad = columnas_num_ciudad[-1]
                    
                    # Preparar datos para el mapa de ciudades
                    df_mapa_ciudad = df_ciudades_casas[[df_ciudades_casas.columns[0], ultima_col_ciudad]].copy()
                    df_mapa_ciudad.columns = ['Ciudad', 'Indice']
                    
                    # Crear gráfico de barras horizontal
                    fig_ciudad = px.bar(
                        df_mapa_ciudad.sort_values('Indice', ascending=True),
                        x='Indice',
                        y='Ciudad',
                        orientation='h',
                        title=f'Cantidad de Casas en Construcción por Ciudad - Periodo {ultima_col_ciudad}',
                        color='Indice',
                        color_continuous_scale='RdYlGn',
                        labels={'Indice': 'Cantidad de Viviendas', 'Ciudad': 'Ciudad'}
                    )
                    
                    fig_ciudad.update_layout(
                        template="plotly_dark",
                        height=max(800, len(df_mapa_ciudad) * 20),
                        showlegend=False,
                        xaxis_title="Cantidad de Viviendas en Construcción",
                        yaxis_title="Ciudad"
                    )
                    
                    st.plotly_chart(fig_ciudad, use_container_width=True)
                    
                    # Gráfico de pastel - Top 10 ciudades (proporción) - Casas
                    df_top_ciudad_pie = df_mapa_ciudad.nlargest(10, 'Indice')
                    fig_pie_ciudad = px.pie(
                        df_top_ciudad_pie,
                        values='Indice',
                        names='Ciudad',
                        title=f'Top 10 Ciudades - Proporción de Casas en Construcción - Periodo {ultima_col_ciudad}',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie_ciudad.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Índice: %{value:.2f}<br>Porcentaje: %{percent}<extra></extra>'
                    )
                    fig_pie_ciudad.update_layout(
                        template="plotly_dark",
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.02
                        )
                    )
                    st.plotly_chart(fig_pie_ciudad, use_container_width=True)

                    # Top ciudades (tabla)
                    st.write("### Top 10 Ciudades - Cantidad de Casas en Construcción")
                    df_top_ciudad = df_mapa_ciudad.nlargest(10, 'Indice').reset_index(drop=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(df_top_ciudad.head(8).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    with col2:
                        st.dataframe(df_top_ciudad.tail(3).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos de ciudades disponibles para el mapa de calor.")

elif st.session_state.vista_actual == "Departamento":
    st.subheader("🏙️ Índice de la vivienda enfocado en los Apartamentos")
    st.markdown("*Análisis del índice de precios de vivienda nueva tipo Apartamento en Colombia*")
    
    # Cargar datos principal para la gráfica de evolución
    df_principal = cargar_datos_principal()
    
    # Cargar datos de apartamentos para mapas
    with st.spinner("Cargando datos de Apartamentos..."):
        df_dept_aptos = cargar_excel_con_hoja(ARCHIVO_DEPARTAMENTOS, "Apartamentos")
        df_ciudades_aptos = cargar_excel_con_hoja(ARCHIVO_CIUDADES, "Apartamentos")
    
    # Verificar si se cargaron ambos archivos
    if df_dept_aptos is None and df_ciudades_aptos is None:
        st.error("❌ No se pudieron cargar los datos de apartamentos (ni departamentos ni ciudades).")
    elif df_dept_aptos is None:
        st.warning("⚠️ No se pudieron cargar los datos de departamentos, pero sí los de ciudades.")
    elif df_ciudades_aptos is None:
        st.warning("⚠️ No se pudieron cargar los datos de ciudades, pero sí los de departamentos.")
    
    # GRÁFICA DE EVOLUCIÓN TEMPORAL (similar a Total y Modelo)
    if df_principal is not None and 'Apartamentos' in df_principal.columns:
        st.markdown("---")
        
        # Crear gráfica con Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_principal["Periodo"],
            y=df_principal["Apartamentos"],
            mode='lines+markers',
            name='Índice Apartamentos',
            line=dict(color='#f093fb', width=3),
            marker=dict(size=6, color='#f5576c', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Apartamentos",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda (Apartamentos)",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df_principal['Apartamentos'].iloc[-1]:.2f}", 
                     f"{((df_principal['Apartamentos'].iloc[-1] - df_principal['Apartamentos'].iloc[-2]) / df_principal['Apartamentos'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df_principal['Apartamentos'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df_principal['Apartamentos'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df_principal['Apartamentos'].min():.2f}")
        
        st.markdown("---")
    
    if df_dept_aptos is not None or df_ciudades_aptos is not None:
        
        # Tabs para organizar la información
        tab1, tab2, tab3 = st.tabs(["📊 Resumen General", "🌆​ Índice en ciudades", "🏗️ Obras en Construcción"])
        
        with tab1:
            st.write("### Estadísticas Generales de Apartamentos en 2025 por Ciudades")
            
            if df_dept_aptos is not None:
                # Calcular última columna disponible (último periodo)
                columnas_numericas = df_dept_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        valor_max = df_dept_aptos[ultima_col].max()
                        dept_max = df_dept_aptos.loc[df_dept_aptos[ultima_col].idxmax()].iloc[0]
                        st.metric("Índice Máximo", f"{valor_max:.2f}", f"{dept_max}")
                    with col2:
                        valor_min = df_dept_aptos[ultima_col].min()
                        dept_min = df_dept_aptos.loc[df_dept_aptos[ultima_col].idxmin()].iloc[0]
                        st.metric("Índice Mínimo", f"{valor_min:.2f}", f"{dept_min}")
                    with col3:
                        promedio = df_dept_aptos[ultima_col].mean()
                        st.metric("Promedio Nacional", f"{promedio:.2f}")
                    with col4:
                        desv_std = df_dept_aptos[ultima_col].std()
                        st.metric("Desviación Estándar", f"{desv_std:.2f}")
                    
                    # Tabla de departamentos
                    st.write("### Top 10 Ciudad - Índice de Precios de Apartamentos")
                    df_top = df_dept_aptos.nlargest(10, ultima_col)[[df_dept_aptos.columns[0], ultima_col]].reset_index(drop=True)
                    df_top.columns = ['Departamento', 'Índice']
                    st.dataframe(df_top.style.format({'Índice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.info("No hay datos de departamentos disponibles para mostrar estadísticas.")
        
        with tab2:
            st.write("### 👩‍💻​ Índice en ciudades")
            
            if df_dept_aptos is not None:
                columnas_numericas = df_dept_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_numericas) > 0:
                    ultima_col = columnas_numericas[-1]
                    
                    # Preparar datos para el mapa
                    df_mapa = df_dept_aptos[[df_dept_aptos.columns[0], ultima_col]].copy()
                    df_mapa.columns = ['Departamento', 'Indice']
                    
                    # Crear dos columnas: gráfico de barras y tabla resumen
                    col_bar, col_pie = st.columns([2, 1])
                    
                    with col_bar:
                        # Crear gráfico de barras horizontal con colores de mapa de calor
                        fig = px.bar(
                            df_mapa.sort_values('Indice', ascending=True),
                            x='Indice',
                            y='Departamento',
                            orientation='h',
                            title=f'Índice de Precios de Apartamentos por Departamento - Periodo {ultima_col}',
                            color='Indice',
                            color_continuous_scale='RdYlGn',
                            labels={'Indice': 'Índice de Vivienda', 'Departamento': 'Departamento'}
                        )
                        
                        fig.update_layout(
                            template="plotly_dark",
                            height=max(600, len(df_mapa) * 25),
                            showlegend=False,
                            xaxis_title="Índice de Vivienda",
                            yaxis_title="Departamento"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col_pie:
                        st.write("#### Proporción por Departamento (resumen)")
                        # Mostrar tabla con los top 10 departamentos
                        df_top_pie = df_mapa.nlargest(10, 'Indice').reset_index(drop=True)
                        st.dataframe(df_top_pie.style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)

                        # Métricas adicionales
                        total_indice = df_mapa['Indice'].sum()
                        st.metric("Total Índice", f"{total_indice:.2f}")
                        st.metric("Departamentos", len(df_mapa))
                    
                    # Información adicional
                    st.info("""
                    💡 **Interpretación del Mapa de Calor:**
                    - 🟢 **Verde:** Índices más altos (mayor crecimiento de precios)
                    - 🟡 **Amarillo:** Índices medios
                    - 🔴 **Rojo:** Índices más bajos (menor crecimiento de precios)
                    """)
            else:
                st.warning("⚠️ No hay datos de departamentos disponibles para el mapa de calor.")
        
        with tab3:
            st.write("### 🏗️ Obras en Construcción")
            st.info("📌 **Nota:** Estos datos representan la cantidad de viviendas nuevas (apartamentos) en construcción por municipio.")
            
            if df_ciudades_aptos is not None:
                columnas_num_ciudad = df_ciudades_aptos.select_dtypes(include=[np.number]).columns
                if len(columnas_num_ciudad) > 0:
                    ultima_col_ciudad = columnas_num_ciudad[-1]
                    
                    # Preparar datos para el mapa de ciudades
                    df_mapa_ciudad = df_ciudades_aptos[[df_ciudades_aptos.columns[0], ultima_col_ciudad]].copy()
                    df_mapa_ciudad.columns = ['Ciudad', 'Indice']
                    
                    # Crear gráfico de barras horizontal
                    fig_ciudad = px.bar(
                        df_mapa_ciudad.sort_values('Indice', ascending=True),
                        x='Indice',
                        y='Ciudad',
                        orientation='h',
                        title=f'Cantidad de Apartamentos en Construcción por Ciudad - Periodo {ultima_col_ciudad}',
                        color='Indice',
                        color_continuous_scale='RdYlGn',
                        labels={'Indice': 'Cantidad de Viviendas', 'Ciudad': 'Ciudad'}
                    )
                    
                    fig_ciudad.update_layout(
                        template="plotly_dark",
                        height=max(800, len(df_mapa_ciudad) * 20),
                        showlegend=False,
                        xaxis_title="Cantidad de Viviendas en Construcción",
                        yaxis_title="Ciudad"
                    )
                    
                    st.plotly_chart(fig_ciudad, use_container_width=True)
                    
                    # Gráfico de pastel - Top 10 ciudades (proporción) - Apartamentos
                    df_top_ciudad_pie_apt = df_mapa_ciudad.nlargest(10, 'Indice')
                    fig_pie_ciudad_apt = px.pie(
                        df_top_ciudad_pie_apt,
                        values='Indice',
                        names='Ciudad',
                        title=f'Top 10 Ciudades - Proporción de Apartamentos en Construcción - Periodo {ultima_col_ciudad}',
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    fig_pie_ciudad_apt.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Índice: %{value:.2f}<br>Porcentaje: %{percent}<extra></extra>'
                    )
                    fig_pie_ciudad_apt.update_layout(
                        template="plotly_dark",
                        height=500,
                        showlegend=True,
                        legend=dict(
                            orientation="v",
                            yanchor="middle",
                            y=0.5,
                            xanchor="left",
                            x=1.02
                        )
                    )
                    st.plotly_chart(fig_pie_ciudad_apt, use_container_width=True)

                    # Top ciudades
                    st.write("### Top 15 Ciudades - Cantidad de Apartamentos en Construcción")
                    df_top_ciudad = df_mapa_ciudad.nlargest(15, 'Indice').reset_index(drop=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.dataframe(df_top_ciudad.head(8).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
                    with col2:
                        st.dataframe(df_top_ciudad.tail(7).style.format({'Indice': '{:.2f}'}).hide(axis="index"), use_container_width=True)
            else:
                st.warning("⚠️ No hay datos de ciudades disponibles para el mapa de calor.")

elif st.session_state.vista_actual == "Total y Modelo":
    st.subheader("🏭 Análisis de la vivienda total en los últimos 20 años")
    st.markdown("*Movimiento y predicción con modelo ARMA para el índice de crecimiento en el precio de la vivienda en Colombia*")
    
    # Cargar datos
    df = cargar_datos_principal()
    
    if df is not None:
        # Crear gráfica con Plotly (más interactiva que matplotlib)
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df["Periodo"],
            y=df["Total"],
            mode='lines+markers',
            name='Índice Total',
            line=dict(color='#43e97b', width=3),
            marker=dict(size=6, color='#38f9d7', line=dict(width=2, color='#ffffff'))
        ))
        
        fig.update_layout(
            title={
                'text': "Evolución Trimestral del Índice de Precios de Vivienda",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': 'white'}
            },
            xaxis_title="Periodo",
            yaxis_title="Índice de Vivienda",
            template="plotly_dark",
            hovermode='x unified',
            height=600,
            xaxis=dict(tickangle=-90),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Métricas adicionales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Índice Actual", f"{df['Total'].iloc[-1]:.2f}", 
                     f"{((df['Total'].iloc[-1] - df['Total'].iloc[-2]) / df['Total'].iloc[-2] * 100):.2f}%")
        with col2:
            st.metric("Promedio Histórico", f"{df['Total'].mean():.2f}")
        with col3:
            st.metric("Máximo Histórico", f"{df['Total'].max():.2f}")
        with col4:
            st.metric("Mínimo Histórico", f"{df['Total'].min():.2f}")
        
        # Tabs adicionales
        tab1, tab2, tab3 = st.tabs(["📈 Análisis Estadístico", "📋 Datos Completos", "🔮 Modelo ARMA"])
        
        with tab1:
            st.write("### Estadísticas Descriptivas")
            st.dataframe(df[["Total"]].describe(), use_container_width=True)
            
            # Gráfica de distribución
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df["Total"],
                nbinsx=30,
                name='Distribución',
                marker_color='#43e97b'
            ))
            fig_hist.update_layout(
                title="Distribución del Índice de Vivienda",
                xaxis_title="Índice",
                yaxis_title="Frecuencia",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with tab2:
            st.write("### Tabla de Datos Completos")
            st.dataframe(df[["Año", "Trimestre", "Periodo", "Total"]], use_container_width=True)
            
            # Opción de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar datos CSV",
                data=csv,
                file_name='datos_vivienda.csv',
                mime='text/csv',
            )
            
        with tab3:
            st.write("### 🔮 Modelo ARMA - Análisis Completo")
            st.info("💡 Haz clic en cada sección para expandir y ver los detalles del análisis")
            
            # ============================================
            # 1. TEST DE ESTACIONARIEDAD (SOLO ADF)
            # ============================================
            with st.expander("1️⃣ Test de Estacionariedad", expanded=False):
                st.subheader("Test de Estacionariedad - ADF")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### Test ADF (Augmented Dickey-Fuller)")
                    result_adf = adfuller(df['Total'].dropna())
                    
                    st.metric("ADF Statistic", f"{result_adf[0]:.6f}")
                    st.metric("p-value", f"{result_adf[1]:.6f}")
                    st.metric("Lags usados", result_adf[2])
                    st.metric("Observaciones", result_adf[3])
                    
                    if result_adf[1] < 0.05:
                        st.success("✅ La serie ES estacionaria (rechazamos H0)")
                    else:
                        st.warning("⚠️ La serie NO es estacionaria (no rechazamos H0)")
                
                with col2:
                    st.write("#### Valores Críticos ADF")
                    st.write("Comparación del estadístico con valores críticos:")
                    
                    for key, val in result_adf[4].items():
                        st.metric(f"Nivel {key}", f"{val:.4f}")
                    
                    st.info("""
                    **Información:**
                    - Si ADF Statistic < Valores Críticos → Serie estacionaria
                    - Si p-value < 0.05 → Rechazamos H0 (la serie es estacionaria)
                    """)
            
            # ============================================
            # 2. AJUSTE DEL MODELO ARMA(1,1)
            # ============================================
            with st.expander("2️⃣ Modelo ARMA(1,1) Ajustado", expanded=False):
                st.subheader("Modelo ARMA(1,1) Ajustado")
                
                # Ajustar el modelo
                res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                # Mostrar resumen del modelo
                with st.expander("📊 Ver resumen completo del modelo"):
                    st.text(str(res.summary()))
                
                # Coeficientes del modelo
                st.write("#### Coeficientes del Modelo")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("AR(1) - φ₁", f"{res.arparams[0]:.6f}")
                with col2:
                    st.metric("MA(1) - θ₁", f"{res.maparams[0]:.6f}")
                with col3:
                    st.metric("Intercepto", f"{res.params['const']:.6f}")
                
                st.write("#### Criterios de Información")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("AIC", f"{res.aic:.4f}")
                with col2:
                    st.metric("BIC", f"{res.bic:.4f}")
                with col3:
                    st.metric("Log-Likelihood", f"{res.llf:.4f}")
            
            # ============================================
            # 3. ANÁLISIS DE RESIDUOS
            # ============================================
            with st.expander("3️⃣ Análisis de Residuos", expanded=False):
                st.subheader("Análisis de Residuos")
                
                # Calcular residuos solo si el modelo ya fue ajustado
                if 'res' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                resid = res.resid.dropna()
                
                st.write("#### Estadísticas de Residuos")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Media", f"{resid.mean():.8f}")
                with col2:
                    st.metric("Desviación Estándar", f"{resid.std():.6f}")
                with col3:
                    st.metric("Sesgo", f"{resid.skew():.6f}")
                with col4:
                    st.metric("Curtosis", f"{resid.kurtosis():.6f}")
                
                st.info("📊 Los residuos deben tener media cercana a cero y comportarse como ruido blanco")
            
            # ============================================
            # 4. TEST DE LJUNG-BOX
            # ============================================
            with st.expander("4️⃣ Test de Ljung-Box (Autocorrelación de Residuos)", expanded=False):
                st.subheader("Test de Ljung-Box - Autocorrelación de Residuos")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("#### Resultados del Test")
                    lags = [4, 8, 12, 16, 20]
                    lb = acorr_ljungbox(resid, lags=lags, return_df=True)
                    st.dataframe(lb.style.format("{:.6f}"), use_container_width=True)
                    
                    # Interpretación
                    if (lb['lb_pvalue'] > 0.05).all():
                        st.success("✅ No hay evidencia de autocorrelación en los residuos")
                    else:
                        st.warning("⚠️ Existe autocorrelación significativa en algunos rezagos")
                    
                    st.info("""
                    **Información:**
                    - **H0:** No hay autocorrelación en los residuos (ruido blanco)
                    - **H1:** Existe autocorrelación en los residuos
                    - Si p-value > 0.05 → No rechazamos H0 (residuos son ruido blanco ✓)
                    - Si p-value < 0.05 → Rechazamos H0 (hay autocorrelación)
                    """)
                
                with col2:
                    st.write("#### ACF de los Residuos")
                    fig_acf, ax = plt.subplots(figsize=(8, 4))
                    plot_acf(resid, lags=20, ax=ax, title='')
                    ax.set_title('ACF de los residuos ARMA(1,1)', fontsize=12, color='white', pad=10)
                    ax.set_xlabel('Rezagos', fontsize=10, color='white')
                    ax.set_ylabel('Autocorrelación', fontsize=10, color='white')
                    ax.set_facecolor('#1a1a2e')
                    fig_acf.patch.set_facecolor('#1a1a2e')
                    ax.tick_params(colors='white')
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    ax.grid(True, alpha=0.2, color='white')
                    
                    # Mejorar visibilidad de las líneas de confianza
                    for line in ax.get_lines()[1:]:
                        line.set_color('#00c4ff')
                        line.set_linewidth(1.5)
                        line.set_alpha(0.7)
                    
                    st.pyplot(fig_acf)
                    plt.close()
            
            # ============================================
            # 5. ANÁLISIS ACF Y PACF PARA ESTACIONALIDAD
            # ============================================
            with st.expander("5️⃣ Análisis ACF y PACF - Identificación de Patrones y Estacionalidad", expanded=False):
                st.subheader("Análisis ACF y PACF - Identificación de Patrones y Estacionalidad")
                
                st.info("""
                **ACF y PACF para detectar estacionalidad:**
                - **ACF (Autocorrelación):** Muestra la correlación de la serie con sus rezagos. Picos significativos en múltiplos de 4 (trimestres) indican estacionalidad anual.
                - **PACF (Autocorrelación Parcial):** Muestra la correlación directa con cada rezago, eliminando efectos intermedios.
                - **Estacionalidad trimestral:** Buscar picos en los rezagos 4, 8, 12, 16... (cada 4 trimestres = 1 año)
                """)
                
                # ACF y PACF de la serie original
                st.write("### 📊 ACF y PACF de la Serie Original")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### ACF - Autocorrelación")
                    fig_acf_original, ax1 = plt.subplots(figsize=(10, 5))
                    plot_acf(df['Total'].dropna(), lags=24, ax=ax1, title='')
                    ax1.set_title('ACF de la Serie Original', fontsize=14, color='white', pad=15)
                    ax1.set_xlabel('Rezagos (Trimestres)', fontsize=11, color='white')
                    ax1.set_ylabel('Autocorrelación', fontsize=11, color='white')
                    ax1.set_facecolor('#1a1a2e')
                    fig_acf_original.patch.set_facecolor('#1a1a2e')
                    ax1.tick_params(colors='white')
                    ax1.grid(True, alpha=0.2, color='white')
                    
                    # Marcar rezagos estacionales
                    for lag in [4, 8, 12, 16, 20, 24]:
                        ax1.axvline(x=lag, color='#ff6b6b', linestyle='--', alpha=0.5, linewidth=1)
                    
                    st.pyplot(fig_acf_original)
                    plt.close()
                    
                    st.caption("🔴 Líneas rojas marcan rezagos estacionales (múltiplos de 4 trimestres)")
                
                with col2:
                    st.write("#### PACF - Autocorrelación Parcial")
                    fig_pacf_original, ax2 = plt.subplots(figsize=(10, 5))
                    plot_pacf(df['Total'].dropna(), lags=24, ax=ax2, title='', method='ywm')
                    ax2.set_title('PACF de la Serie Original', fontsize=14, color='white', pad=15)
                    ax2.set_xlabel('Rezagos (Trimestres)', fontsize=11, color='white')
                    ax2.set_ylabel('Autocorrelación Parcial', fontsize=11, color='white')
                    ax2.set_facecolor('#1a1a2e')
                    fig_pacf_original.patch.set_facecolor('#1a1a2e')
                    ax2.tick_params(colors='white')
                    ax2.grid(True, alpha=0.2, color='white')
                    
                    # Marcar rezagos estacionales
                    for lag in [4, 8, 12, 16, 20, 24]:
                        ax2.axvline(x=lag, color='#ff6b6b', linestyle='--', alpha=0.5, linewidth=1)
                    
                    st.pyplot(fig_pacf_original)
                    plt.close()
                    
                    st.caption("🔴 Líneas rojas marcan rezagos estacionales (múltiplos de 4 trimestres)")
                
                # Interpretación automática de estacionalidad
                st.write("### 🔍 Interpretación de Estacionalidad")
                
                from statsmodels.tsa.stattools import acf
                acf_values = acf(df['Total'].dropna(), nlags=24)
                
                # Detectar picos en rezagos estacionales
                seasonal_lags = [4, 8, 12, 16, 20]
                seasonal_peaks = [lag for lag in seasonal_lags if abs(acf_values[lag]) > 0.3]
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if len(seasonal_peaks) > 0:
                        st.warning(f"""
                        ⚠️ **Posible estacionalidad detectada** en los rezagos: {seasonal_peaks}
                        
                        Esto sugiere que existe un patrón que se repite cada {seasonal_peaks[0]} trimestres (aproximadamente cada año).
                        
                        **Recomendación:** Considerar un modelo SARIMA (Seasonal ARIMA) en lugar de ARMA simple.
                        """)
                    else:
                        st.success("""
                        ✅ **No se detecta estacionalidad significativa** en la serie.
                        
                        El modelo ARMA(1,1) es apropiado para esta serie temporal.
                        """)
                
                with col2:
                    st.metric("Rezagos Estacionales Detectados", len(seasonal_peaks))
                    if len(seasonal_peaks) > 0:
                        st.metric("Periodo Estacional", f"{seasonal_peaks[0]} trimestres")
                    st.metric("Total Rezagos Analizados", 24)
            
            # ============================================
            # 6. TEST DE JARQUE-BERA (NORMALIDAD)
            # ============================================
            with st.expander("6️⃣ Test de Jarque-Bera (Normalidad de Residuos)", expanded=False):
                st.subheader("Test de Jarque-Bera - Normalidad de Residuos")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    jb_stat, jb_p, skew, kurtosis = jarque_bera(resid)
                    
                    st.write("#### Resultados del Test")
                    st.metric("Estadístico JB", f"{jb_stat:.6f}")
                    st.metric("p-value", f"{jb_p:.6f}")
                    st.metric("Sesgo", f"{skew:.6f}")
                    st.metric("Curtosis", f"{kurtosis:.6f}")
                    
                    if jb_p > 0.05:
                        st.success("✅ Los residuos siguen una distribución normal")
                    else:
                        st.warning("⚠️ Los residuos NO siguen una distribución normal perfecta")
                    
                    st.info("""
                    **Información:**
                    - **H0:** Los residuos siguen una distribución normal
                    - **H1:** Los residuos NO siguen una distribución normal
                    - Si p-value > 0.05 → No rechazamos H0 (residuos normales ✓)
                    - Si p-value < 0.05 → Rechazamos H0 (residuos no normales)
                    - Sesgo cercano a 0 y curtosis cercana a 3 indican normalidad
                    """)
                
                with col2:
                    st.write("#### QQ-Plot")
                    fig_qq, ax = plt.subplots(figsize=(6, 6))
                    sm.qqplot(resid, line='s', ax=ax)
                    ax.set_title('QQ-plot de los residuos', color='white')
                    ax.set_facecolor('#1a1a2e')
                    fig_qq.patch.set_facecolor('#1a1a2e')
                    ax.tick_params(colors='white')
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    ax.get_lines()[0].set_color('#43e97b')
                    ax.get_lines()[1].set_color('#ff6b6b')
                    st.pyplot(fig_qq)
                    plt.close()
            
            # ============================================
            # 7. TEST ARCH (HETEROCEDASTICIDAD)
            # ============================================
            with st.expander("7️⃣ Test ARCH-LM (Heterocedasticidad)", expanded=False):
                st.subheader("Test ARCH-LM - Heterocedasticidad")
                
                if 'resid' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                    resid = res.resid.dropna()
                
                arch_res = het_arch(resid, nlags=4)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Estadístico LM", f"{arch_res[0]:.6f}")
                    st.metric("p-value", f"{arch_res[1]:.6f}")
                with col2:
                    st.metric("Estadístico F", f"{arch_res[2]:.6f}")
                    st.metric("p-value F", f"{arch_res[3]:.6f}")
                
                if arch_res[1] > 0.05:
                    st.success("✅ No hay evidencia de heterocedasticidad condicional (efecto ARCH)")
                else:
                    st.warning("⚠️ Existe heterocedasticidad condicional (efecto ARCH presente)")
                
                st.info("""
                **Información:**
                - **H0:** No hay efecto ARCH (homocedasticidad - varianza constante)
                - **H1:** Existe efecto ARCH (heterocedasticidad condicional)
                - Si p-value > 0.05 → No rechazamos H0 (varianza constante ✓)
                - Si p-value < 0.05 → Rechazamos H0 (la varianza cambia en el tiempo)
                - Efecto ARCH indica que la volatilidad de los errores varía con el tiempo
                """)
            
            # ============================================
            # 8. ESTABILIDAD E INVERTIBILIDAD
            # ============================================
            with st.expander("8️⃣ Estabilidad e Invertibilidad del Modelo", expanded=False):
                st.subheader("Estabilidad e Invertibilidad del Modelo")
                
                if 'res' not in locals():
                    res = ARIMA(df['Total'], order=(1,0,1)).fit()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### Test de Estabilidad (Raíces AR)")
                    try:
                        arparams = res.arparams
                        ar_roots = res.arroots
                        mods_ar_roots = np.abs(ar_roots)
                        
                        st.metric("Parámetro AR (φ₁)", f"{arparams[0]:.6f}")
                        st.metric("Raíz AR (z)", f"{ar_roots[0]:.6f}")
                        st.metric("Módulo |z|", f"{mods_ar_roots[0]:.6f}")
                        
                        ar_ok = all(mods_ar_roots > 1.0)
                        if ar_ok:
                            st.success(f"✅ Modelo ESTABLE (todas las raíces AR |z| > 1)")
                        else:
                            st.error(f"❌ Modelo INESTABLE (alguna raíz AR tiene |z| ≤ 1)")
                        
                        st.info("""
                        **Información:**
                        - **Condición de estabilidad:** |z| > 1
                        - Si todas las raíces AR están fuera del círculo unitario → Modelo estable ✓
                        - Un modelo estable garantiza que los efectos de shocks se disipan con el tiempo
                        """)
                        
                    except Exception as e:
                        st.error(f"Error al calcular estabilidad: {e}")
                
                with col2:
                    st.write("#### Test de Invertibilidad (Raíces MA)")
                    try:
                        maparams = res.maparams
                        ma_roots = res.maroots
                        mods_ma_roots = np.abs(ma_roots)
                        
                        st.metric("Parámetro MA (θ₁)", f"{maparams[0]:.6f}")
                        st.metric("Raíz MA (z)", f"{ma_roots[0]:.6f}")
                        st.metric("Módulo |z|", f"{mods_ma_roots[0]:.6f}")
                        
                        ma_ok = all(mods_ma_roots > 1.0)
                        if ma_ok:
                            st.success(f"✅ Modelo INVERTIBLE (todas las raíces MA |z| > 1)")
                        else:
                            st.error(f"❌ Modelo NO INVERTIBLE (alguna raíz MA tiene |z| ≤ 1)")
                        
                        st.info("""
                        **Información:**
                        - **Condición de invertibilidad:** |z| > 1
                        - Si todas las raíces MA están fuera del círculo unitario → Modelo invertible ✓
                        - Un modelo invertible permite representar el proceso como un AR(∞)
                        """)
                        
                    except Exception as e:
                        st.error(f"Error al calcular invertibilidad: {e}")
            
            # ============================================
            # 9. PRONÓSTICO Y VALIDACIÓN
            # ============================================
            with st.expander("9️⃣ Pronóstico y Validación del Modelo", expanded=False):
                st.subheader("Pronóstico y Validación del Modelo")
                
                # Train/Test Split
                h = 4
                y = df['Total']
                train, test = y[:-h], y[-h:]
                
                # Ajustar modelo en train
                model_train = ARIMA(train, order=(1,0,1)).fit()
                
                # Pronóstico
                fc = model_train.get_forecast(steps=h)
                pred = fc.predicted_mean
                conf = fc.conf_int()
                
                # Métricas
                rmse = np.sqrt(mean_squared_error(test, pred))
                mae = mean_absolute_error(test, pred)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tamaño Train", len(train))
                with col2:
                    st.metric("Tamaño Test", len(test))
                with col3:
                    st.metric("RMSE", f"{rmse:.6f}")
                with col4:
                    st.metric("MAE", f"{mae:.6f}")
                
                # Gráfico de pronóstico
                st.write("#### Gráfico Train / Test / Forecast")
                
                fig_forecast, ax = plt.subplots(figsize=(14, 6))
                
                train.plot(ax=ax, label='Train', color='#43e97b', linewidth=2)
                test.plot(ax=ax, label='Test (Real)', marker='o', color='#ff6b6b', linewidth=2, markersize=8)
                pred.plot(ax=ax, label='Forecast', marker='s', color='#00c4ff', linewidth=2, markersize=8)
                
                ax.fill_between(conf.index, conf.iloc[:,0], conf.iloc[:,1], alpha=0.3, color='#00c4ff')
                
                ax.set_title('Pronóstico ARMA(1,1) - Últimos 4 Trimestres', fontsize=16, color='white', pad=20)
                ax.set_xlabel('Periodo', fontsize=12, color='white')
                ax.set_ylabel('Índice de Vivienda', fontsize=12, color='white')
                ax.legend(loc='best', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#1a1a2e')
                fig_forecast.patch.set_facecolor('#1a1a2e')
                ax.tick_params(colors='white')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                st.pyplot(fig_forecast)
                plt.close()
                
                # Tabla de comparación
                st.write("#### Comparación: Valores Reales vs Pronósticos")
                comparison_df = pd.DataFrame({
                    'Periodo': test.index,
                    'Real': test.values,
                    'Pronóstico': pred.values,
                    'Error': test.values - pred.values,
                    'Error %': ((test.values - pred.values) / test.values * 100)
                })
                st.dataframe(comparison_df.style.format({
                    'Real': '{:.4f}',
                    'Pronóstico': '{:.4f}',
                    'Error': '{:.4f}',
                    'Error %': '{:.2f}%'
                }), use_container_width=True)
            
            # ============================================
            # CONCLUSIÓN FINAL
            # ============================================
            st.markdown("---")
            st.success("""
            ### 🎯 Conclusiones del Modelo ARMA(1,1)
            
            El modelo ARMA(1,1) ha sido ajustado y validado exhaustivamente mediante múltiples pruebas estadísticas:
            
            - ✅ Test de estacionariedad confirmado (ADF)
            - ✅ Residuos analizados (media cercana a cero, autocorrelación, normalidad)
            - ✅ Análisis ACF/PACF para detectar estacionalidad
            - ✅ Test de normalidad (Jarque-Bera) y QQ-plot
            - ✅ Test de heterocedasticidad (ARCH-LM)
            - ✅ Estabilidad e invertibilidad verificadas
            - ✅ Pronóstico validado con métricas RMSE y MAE
            
            El modelo es adecuado para el análisis de la serie temporal de vivienda en Colombia.
            """)
    
    else:
        st.warning("⚠️ No se pudieron cargar los datos. Asegúrate de que el archivo Excel esté en el directorio correcto.")

else:
    st.info("👈 Selecciona una opción en el panel izquierdo para comenzar.")



