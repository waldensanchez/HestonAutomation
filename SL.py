from HestonVolatilities import HestonImpliedVolatility
from HestonPrices import HestonPrice
from datetime import datetime
import streamlit as st


# Configurations
st.set_option('deprecation.showPyplotGlobalUse', False)

# Images
col1, col2 = st.columns(2)
with col1:
    st.image("https://oci02.img.iteso.mx/Identidades-De-Instancia/ITESO/Logos%20ITESO/Logo-ITESO-Principal-FondoAzul.png ", use_column_width=True)
with col2:
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTdte_kajaSBaesIKbOOtEEfSKtd7g0HiVz07OfXn1Lc23kKgAI7idC0010DyRA4Z9M3xo&usqp=CAU.png ", use_column_width=True)

# Code
st.title('Heston')
st.subheader('Calculadora de opciones europeas')

selected_asset = st.text_input('Introduzca el ticker','AAPL')
call_or_put = st.selectbox('Call / Put',['Call','Put'])


tab3, tab4= st.tabs(["Volatilidad suavizada", "Precio"])
with tab3:
    if st.button('Encontrar volatilidad suavizada', use_container_width=True):
        bar = st.progress(0)
        HestonVolatility = HestonImpliedVolatility(selected_asset)
        bar.progress(40)
        HestonVolatility.get_dividend_yield() 
        HestonVolatility.get_risk_free()
        HestonVolatility.opt_type(call_or_put)
        bar.progress(70)
        HestonVolatility.get_results()
        bar.progress(100)

        st.subheader('Volatilidad Implícita')
        tab1, tab2= st.tabs(["Tabla", " 📈"])
        with tab1:
            st.dataframe(data=HestonVolatility.table, hide_index=True)
        with tab2:
            st.plotly_chart(HestonVolatility.volatility_surface(), use_container_width=True)

with tab4:
    HestonPrices = HestonPrice(selected_asset)
    HestonPrices.get_mkt_data(risk_free_rate=.00525)
    HestonPrices.get_dividend_yield()
    HestonPrices.get_closest_most_common_option(call_or_put)

    st.subheader('Precio')

    col1, col2 = st.columns(2)
    with col1:
        calculation_date = st.date_input("Valuation Date", value=datetime.today())
        strike_price = st.number_input('Strike', value=HestonPrices.common_strike, max_value=200000.0, step=1.0)
    with col2:
        maturity_date = st.date_input("Maturity", value=HestonPrices.closest_exp_date)
        spot_price = st.number_input('Spot', min_value=0.0, value=HestonPrices.spot_price, max_value=200000.0, step=1.0)


    HestonPrices.get_prices(strike_price, spot_price)
    HestonPrices.get_dates(calculation_date=calculation_date, maturity_date=maturity_date)
    with st.expander("Personalizar parámetros"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            v0 = st.number_input(f'$V_0$', value=None, placeholder=f'$Óptimo$')
        with col2:
            theta = st.number_input(f'$\Theta$', value=None, placeholder=f"$Óptimo$")
        with col3:
            epsilon = st.number_input(f'$\epsilon$', value=None, placeholder=f"$Óptimo")
        with col4:
            rho = st.number_input(f'$\Rho$', value=None, placeholder=f"$Óptimo$")

    if st.button('Calcular precio', use_container_width=True):   
        HestonPrices.parameter_optimizer(.1,.1,.1,.1,.1)
        HestonPrices.calculate_heston_pricing()
        st.write('Precio con Heston:', HestonPrices.heston_price)

