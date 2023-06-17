sudo apt install python3-pip  python3-pycurl -y
pip3 install virtualenv
virtualenv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
