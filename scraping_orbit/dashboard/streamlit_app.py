import streamlit as st
import streamlit as st
import pandas as pd
from io import StringIO
from llmsherpa.readers import LayoutPDFReader
class ScrapingOrbit:
    def __init__(self):
        self.test = False

    def initialize_dashboard(self):
        st.write('working')
        x = st.slider("Select a value")
        st.write(x, "squared is", x * x)
        doc_container = st.container()

        self.document_container(element=doc_container)

    def document_container(self,element):
        with element:
            uploaded_file = st.file_uploader("Choose a file")
            if uploaded_file is not None:
                pass


if __name__ == '__main__':
    scraping_orbit_class = ScrapingOrbit()
    scraping_orbit_class.initialize_dashboard()
