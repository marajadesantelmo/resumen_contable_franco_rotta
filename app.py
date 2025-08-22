import streamlit as st
st.set_page_config(page_title="Resumen Contable", layout="wide")
from streamlit_cookies_manager import EncryptedCookieManager
import pandas as pd

# Import page modules
import app_resumen_vencido
import app_mes_corriente
import app_historico

# Apply custom styling for dataframes - darker background
st.markdown("""
<style>
    .stDataFrame {
        background-color: #d0d4dc;
        padding: 10px;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Login function
CREDENTIALS = {"franco": "reishi", "admin": "admin"}

def login(username, password):
    return CREDENTIALS.get(username) == password

def main():
    # Initialize cookies manager
    cookies = EncryptedCookieManager(prefix="resumen_contable_", password="secure_password_here")
    
    if not cookies.ready():
        st.stop()
    
    # Check if user is already logged in
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = cookies.get("logged_in") == "True"
    if 'username' not in st.session_state:
        st.session_state.username = cookies.get("username", "")
    
    if not st.session_state.logged_in:
        st.title("Resumen Contable - Login")
        
        # Simple login form
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                
                if st.button("Ingresar", key="login_button"):
                    if login(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        cookies["logged_in"] = "True"
                        cookies["username"] = username
                        cookies.save()
                        st.success("¡Bienvenido/a!")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
    else:
        # Set up navigation
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Resumen Mes Vencido"
        
        # Navigation sidebar
        st.sidebar.title("Navegación")
        #pages = ["Resumen Mes Vencido", "Mes Corriente", "Histórico"]
        pages = ["Resumen Mes Vencido", "Histórico"]
        current_page = st.sidebar.radio("Seleccione sección:", pages, index=pages.index(st.session_state.current_page))
        st.session_state.current_page = current_page
        
        # Display selected page
        if current_page == "Resumen Mes Vencido":
            app_resumen_vencido.show_page()
        elif current_page == "Mes Corriente":
            app_mes_corriente.show_page()
        elif current_page == "Histórico":
            app_historico.show_page()

        # Add logout button
        if st.sidebar.button("Cerrar sesión"):
            cookies["logged_in"] = "False"
            cookies.pop("username", None)
            cookies.save()
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

if __name__ == "__main__":
    main()