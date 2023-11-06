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

if st.button('Encontrar volatilidad suavizada'):
    bar = st.progress(0)
    heston = Heston(selected_asset)
    heston.get_dividend(0) # Corregir dividendo
    heston.opt_type(call_or_put)
    bar.progress(70)
    heston.get_results()
    st.dataframe(data=heston.table, hide_index=True)
    bar.progress(100)
    if simple_raph:
        st.pyplot(heston.plot_simply())