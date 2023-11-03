import streamlit as st
import pandas as pd
from Heston import Heston

def input_csv(uploaded_file):
    return pd.read_csv(uploaded_file)

def output_txt(result, filename="/tmp/output.txt"):
    with open(filename, "w") as f:
        f.write(result)
    return filename

def main():
    st.title('Heston Model Volatility Calculator')

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file is not None:
        df = input_csv(uploaded_file)
        result = Heston(df)

        # Save the result to a temporary file and provide a download link
        result_file_path = output_txt(result)
        with open(result_file_path, "rb") as f:
            st.download_button(
                label="Download TXT",
                data=f,
                file_name="output.txt",
                mime="text/plain"
            )

        st.success('Processing complete! Click the download button to get the TXT file.')

if __name__ == "__main__":
    main()
