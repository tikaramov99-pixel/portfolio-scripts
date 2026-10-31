#!/bin/bash
cd "$(dirname "$0")"
echo
echo " Confidential data, analysed offline"
echo " The first start installs 3 Python packages (needs internet, once). After that it works offline."
echo
python3 -m pip install --quiet -r requirements.txt
python3 -m streamlit run app.py
