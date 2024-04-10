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
import romkan
import re

max_page_idx = 5
base_url = 'https://chunom.org/pages/grade/{idx}/'
nom_base_url = "https://chunom.org/pages/{unihan_code}/"
unihan_base_url = "https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint={unihan_code}"
jisho_search_url = "https://jisho.org/search/{unihan}%23kanji"
max_try = 3
nom_ls = []

# %%

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

nom_df.to_pickle("./kanji-chunom-mapping/nom_df_url.pickle")
nom_df = pd.read_pickle("./kanji-chunom-mapping/nom_df_url.pickle")

# %%
# Async to extrac unihan from unicode.org
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

# Async to extrac japanese kanji details from jisho
async def extractJapanese(df, url):
    async with aiohttp.ClientSession() as session:
        try:
            print(f"extracting {url}")
            resp = await session.get(url)
            content = await resp.text()
            soup = BeautifulSoup(content)
            if not soup.find("div", {"class": "kanji-details__main-meanings"}):
                print(f"url {url} cannot find any kanji")
                df.loc[df['jisho_url'] == url, ["kanji_eng","jlpt_level","jisho_kanji_word"]] = [[""]*3]
            else:
                kanji_eng = soup.find("div", {"class": "kanji-details__main-meanings"}).text.strip("\n ")
                on_read_children = soup.find("dt", string="On:")
                if on_read_children:
                    on_read_children = on_read_children.parent.findChild("dd").findChildren("a")
                    on_read_children_ls = [a.text for a in on_read_children]  
                    on_read_children_ls = [f"{on}|{romkan.to_roma(on)}" for on in on_read_children_ls]  
                else:
                    on_read_children_ls = []
                jlpt_level = soup.find("div", {"class": "jlpt"})
                if jlpt_level:
                    jlpt_level = jlpt_level.findChild('strong').text
                    
                jisho_kanji_word = "https:" + soup.find("a", string=re.compile('Words containing')).attrs["href"]

                df.loc[df['jisho_url'] == url, [f"on_read_{i+1}" for i in range(len(on_read_children_ls))] + ["kanji_eng","jlpt_level","jisho_kanji_word"]] = [on_read_children_ls + [kanji_eng, jlpt_level, jisho_kanji_word]]
            await asyncio.sleep(3)

        except Exception as e:
            print(f"Error getting {url} due to error {e}")
            
            # print(content)

# Async to extrac nom from nomorg
# this source lacks of many english and vietnamese translation
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

# Async main
max_try = 2
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
            
# for loop to extract nom from chunom.org
for url in nom_df[nom_df["nom_viet"].isnull()]["nom_url"]:
    print(f"querying from {url}")
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    find_ls = soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
    nom_eng = find_ls[-2]
    nom_viet = find_ls[1]
    nom_df.loc[nom_df['nom_url'] == url, ["nom_eng","nom_viet"]] = [[nom_eng, nom_viet]]


loop = asyncio.new_event_loop()
loop.run_until_complete(main(nom_df, extractUnihan, 'unihan_url', 'unihan'))
nom_df['jisho_url'] = nom_df.unihan.apply(lambda c: jisho_search_url.format(unihan = c))
loop.run_until_complete(main(nom_df, extractJapanese, 'jisho_url', 'kanji_eng'))
# loop.run_until_complete(main(nom_df, extractNom, 'nom_url', 'unihan'))
loop.close()

# %%

res = requests.get(jisho_search_url.format(unihan = "日"))
soup = BeautifulSoup(res.text)
kanji_eng = soup.find("div", {"class": "kanji-details__main-meanings"}).text.strip("\n ")
on_read_children = soup.find("dt", string="On:").parent.findChild("dd").findChildren("a")
on_read_children_ls = [a.text for a in on_read_children]  
on_read_children_ls = [f"{on}|{romkan.to_roma(on)}" for on in on_read_children_ls]  
jlpt_level = soup.find("div", {"class": "jlpt"})
if jlpt_level:
    jlpt_level = jlpt_level.findChild('strong').text

jisho_kanji_word = f"https://jisho.org/search/*{unihan}*"
# nom_df['unihan'] = nom_df.unihan_url.progress_apply(lambda u: extractUnihan(u))



nom_href_ls = [href_base_url.format(nom_href = nom.attrs["href"]) for nom in nom_ls]
nom_href_ls = list(set(nom_href_ls)) #rm dup

# Getting specific details

res = requests.get(nom_href_ls[11])
res = requests.get('https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint=559D')
res = requests.get('https://jisho.org/search/産%23kanji')

soup = BeautifulSoup(res.text)

# jp_on_td = 
soup.find("b", string="Definition").parent.parent.findChild("td", {"align" : "left"}).text
jp_on = jp_on_td.findNext("td")

jp_on.text



soup.find("span", {"class": "glyph_meaning"}).text.strip("\n\t")
soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
# %%
