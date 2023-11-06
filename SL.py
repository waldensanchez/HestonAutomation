import streamlit as st
from HestonVolatilitiesUI import HestonModule as Heston

# Configurations
st.set_option('deprecation.showPyplotGlobalUse', False)
# Code

st.title('Volatilidad Suavizada con Heston')
st.subheader('ITESO')

selected_asset = st.text_input('Introduzca el ticker','AAPL')
call_or_put = st.selectbox('Call / Put',['Call','Put'])
simple_raph = st.toggle('Simple graph', value=False)
adj_graph = st.toggle('Adjusted graph', value=False)

if st.button('Encontrar volatilidad suavizada'):
    heston = Heston(selected_asset)
    heston.get_dividend(0) # Corregir dividendo
    heston.opt_type(call_or_put)
    heston.get_results()

    if simple_raph:
        st.pyplot(heston.plot_simply())

    if adj_graph:
        st.pyplot(heston.adj_pol())
