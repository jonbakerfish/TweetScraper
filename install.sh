########################### build conda env ################################
conda init
source ~/.bashrc
conda create -n tweetscraper python=3.7.7 -y

########################### activate env ###################################
eval "$(conda shell.bash hook)"
conda activate tweetscraper
which python

########################### install deps env ###############################
conda install -y -c conda-forge scrapy ipython ipdb

########################### install scrapy-selenium ########################
sudo apt update
sudo apt install firefox-geckodriver firefox -y
pip install scrapy-selenium