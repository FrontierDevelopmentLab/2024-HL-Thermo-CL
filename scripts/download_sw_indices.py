import wget
url1 = 'https://sol.spacenvironment.net/JB2008/indices/SOLFSMY.TXT'
url2 = 'https://sol.spacenvironment.net/JB2008/indices/DTCFILE.TXT'
url3 = 'https://www.celestrak.com/SpaceData/SW-All.csv'
download_dir=''
wget_out_set_1 = wget.download(url1,download_dir)
print(f'downloaded at {wget_out_set_1}')
wget_out_set_2 = wget.download(url2,download_dir)
print(f'downloaded at {wget_out_set_2}')
wget_out_celestrack = wget.download(url3,download_dir)
print(f'downloaded at {wget_out_celestrack}')
