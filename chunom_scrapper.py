# %%

import sys
import pathlib
import os
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import asyncio
import aiohttp

max_page_idx = 5
base_url = 'https://chunom.org/pages/grade/{idx}/'
nom_base_url = "https://chunom.org/pages/{unihan_code}/"
unihan_base_url = "https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint={unihan_code}"
max_try = 3
nom_ls = []

# Getting list of nom <a> element

for i in range(max_page_idx):
    url = base_url.format(idx = i)
    print(f'getting {url}')
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    nom_ls += soup.find_all("a", {"class":"nom glyph-box"})

# %%

# Creating df of nom with respective url

nom_df = pd.DataFrame({"unihan_code" : [nom.attrs["href"] for nom in nom_ls]})
nom_df.unihan_code = nom_df.unihan_code.apply(lambda s: s.split("/")[2])
nom_df = nom_df.drop_duplicates()
nom_df['nom_url'] = nom_df.unihan_code.apply(lambda c: nom_base_url.format(unihan_code = c))
nom_df['unihan_url'] = nom_df.unihan_code.apply(lambda c: unihan_base_url.format(unihan_code = c))

nom_df.to_pickle("./nom_df_url.pickle")
nom_df = pd.read_pickle("./nom_df_url.pickle")

# %%

async def extractNom(df, url):
    async with aiohttp.ClientSession() as session:
        try:
            print(f"extracting {url}")
            resp = await session.get(url)
            content = await resp.text()
            soup = BeautifulSoup(content)
            df.loc[df['unihan_url'] == url, 'unihan'] = soup.find("font", {"size" : 7}).text
            await asyncio.sleep(3)
        except:
            print(url)
            print(content)

async def extractUnihan(df, url):
    async with aiohttp.ClientSession() as session:
        try:
            print(f"extracting {url}")
            resp = await session.get(url)
            content = await resp.text()
            soup = BeautifulSoup(content)
            df.loc[df['unihan_url'] == url, 'unihan'] = soup.find("font", {"size" : 7}).text
            await asyncio.sleep(3)
        except:
            print(url)
            print(content)

async def extractNom(df, url):
    async with aiohttp.ClientSession() as session:
        try:
            print(f"extracting {url}")
            resp = await session.get(url)
            content = await resp.text()
            soup = BeautifulSoup(content)
            unihan = soup.find("font", {"face":"Nom Na Tong"}).text.strip(" ")
            nom_eng = soup.find("b", string="Definition").parent.parent.findChild("td", {"align" : "left"}).text
            nom_viet = soup.find("b", string="Vietnamese ").parent.parent.findChild("td", {"align" : "left"}).text
            find_ls = soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
            nom_eng = find_ls[-2]
            nom_viet = find_ls[1]
            df.loc[df['nom_url'] == url, ["nom_viet_translation","nom_eng_translation"]] = [[find_ls[1], find_ls[-2]]]
            df.loc[df['nom_url'] == url, ["unihan","nom_eng","nom_viet","hanviet_pron"]] = [[unihan, nom_eng, nom_viet, hanviet_pron]]
        except:
            print(url)
            print(content)

async def main(df,func, url_str, target_col):
    if target_col not in df:
        df[target_col] = np.nan
    try_n = 0
    while df[target_col].isnull().any() and try_n<max_try:
        try:
            await asyncio.gather(*[func(df, url) for url in df[df[target_col].isnull()][url_str]])
        except:
            print(f"Failed to get complete data. Still {df[target_col].isnull().sum()} is null, retry #{try_n}")
            try_n +=1
            await asyncio.sleep(5)
            continue
            
# for i in tqdm(range(len(nom_df[nom_df["nom_viet"].isnull()]["nom_url"]))):
    # url = nom_df[nom_df["nom_viet"].isnull()]["nom_url"].iloc[i]
for url in nom_df[nom_df["nom_viet"].isnull()]["nom_url"]:
    print(f"querying from {url}")
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    find_ls = soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
    nom_eng = find_ls[-2]
    nom_viet = find_ls[1]
    nom_df.loc[nom_df['nom_url'] == url, ["nom_eng","nom_viet"]] = [[nom_eng, nom_viet]]


        

# async def main2(df,func, url_str, target_col):
#     await asyncio.gather(*[func(df, url) for url in df[df[targ url_str])

# [url for url in nom_df[nom_df['unihan'].isnull()]['unihan_url' ]]


loop = asyncio.new_event_loop()
loop.run_until_complete(main(nom_df, extractUnihan, 'unihan_url', 'unihan'))
loop.run_until_complete(main(nom_df, extractNom, 'nom_url', 'unihan'))
loop.close()


nom_df['unihan'] = nom_df.unihan_url.progress_apply(lambda u: extractUnihan(u))



nom_href_ls = [href_base_url.format(nom_href = nom.attrs["href"]) for nom in nom_ls]
nom_href_ls = list(set(nom_href_ls)) #rm dup

# Getting specific details

res = requests.get(nom_href_ls[11])
res = requests.get('https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint=559D')
res = requests.get('https://www.nomfoundation.org/common/nom_details.php?codepoint=4E94&img=1&uiLang=en')

soup = BeautifulSoup(res.text)

# jp_on_td = 
soup.find("b", string="Definition").parent.parent.findChild("td", {"align" : "left"}).text
jp_on = jp_on_td.findNext("td")

jp_on.text



soup.find("span", {"class": "glyph_meaning"}).text.strip("\n\t")
soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
# %%
