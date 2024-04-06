# %%

import sys

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import numpy as np
import asyncio
import aiohttp

tqdm.pandas()

max_page_idx = 5
base_url = 'https://chunom.org/pages/grade/{idx}/'
nom_base_url = "https://chunom.org/pages/{unihan_code}/"
unihan_base_url = "https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint={unihan_code}"
url2 = 'https://chunom.org/pages/275F1/'
url3 = 'https://stackoverflow.com/questions/68217801/page-keeps-loading-for-a-very-long-time-even-after-an-explicit-wait-selenium-py'

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

# %%


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

async def extractNomToVietEng(df, url):
    async with aiohttp.ClientSession() as session:
        print(f"extracting {url}")
        resp = await session.get(url)
        content = await resp.text()
        soup = BeautifulSoup(content)
        find_ls = soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
        df.loc[df['nom_url'] == url, ["nom_viet_translation","nom_eng_translation"]] = [[find_ls[1], find_ls[-2]]]


async def main(df,func, url_str, target_col):
    if target_col not in df:
        df[target_col] = np.nan
    while target_col
    try:
        await asyncio.gather(*[func(df, url) for url in df[url_str] if df[df[url_str] == url, target_col]])

async def main2(df, url_str ):
    await asyncio.gather(*[extractUnihan(df, url) for url in df[url_str]])



loop = asyncio.new_event_loop()
loop.run_until_complete(main2(nom_df, 'unihan_url'))
loop.run_until_complete(main(nom_df, extractUnihan, 'unihan_url'))
loop.run_until_complete(main(nom_df, extractNomToVietEng, 'nom_url'))
loop.close()


nom_df['unihan'] = nom_df.unihan_url.progress_apply(lambda u: extractUnihan(u))



nom_href_ls = [href_base_url.format(nom_href = nom.attrs["href"]) for nom in nom_ls]
nom_href_ls = list(set(nom_href_ls)) #rm dup

# Getting specific details

res = requests.get(nom_href_ls[11])
res = requests.get('https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint=559D')
res = requests.get('https://www.unicode.org/cgi-bin/GetUnihanData.pl?codepoint=229DA')
soup = BeautifulSoup(res.text)

jp_on_td = soup.find("td", string="Vietnamese")
jp_on = jp_on_td.findNext("td")

jp_on.text



soup.find("span", {"class": "glyph_meaning"}).text.strip("\n\t")
soup.find("span", {"class": "glyph_meaning"}).parent.text.split("\n\t")
# %%
