import os
import subprocess
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import aiofiles

'''
TODO:
fix font
Download all fictions from profile
Download all favourites from profile
Add emailing options
'''


async def get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def get_chapter_text(chapter_url):
    html = await get(chapter_url)
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1', class_='font-white', style='margin-top: 10px')
    print(title.text)
    title = str(title)
    note = soup.find('div', class_='portlet-body author-note')
    if note is not None:
        note = str(note).replace('<div class="spoiler" data-class="spoiler" data-caption="Spoiler">', ">! ")
        note = note.replace('<td style="width: 98.6971%">', '<td style="width: 98.6971%; background-color: #00436e">')
        note = note.replace('<td style="width: 98.4211%">', '<td style="width: 98.4211%; background-color: #00436e">')

    text = str(soup.find_all("div", class_="chapter-inner chapter-content")[0])
    text = text.replace('<div class="spoiler" data-class="spoiler" data-caption="Spoiler">', ">! ")
    text = text.replace("<p> </p>", "")
    text = text.replace('<td style="width: 99.1477%">', '<td style="width: 98.1477%; background-color: #00436e">')
    text = text.replace('<td style="width: 99.1477%; text-align: center">', '<td style="width: 98.6971%; text-align: center; background-color: #00436e">')
    text = text.replace('<td style="width: 98.6971%">', '<td style="width: 98.6971%; background-color: #00436e">')

    return text, note, title


async def get_chapter_html(chapter_url):
    return await get(chapter_url)


async def get_next_chapter_url(chapter_url):
    html = await get(chapter_url)
    soup = BeautifulSoup(html, 'html.parser')
    try:
        next_link = soup.find_all('a', class_='btn btn-primary col-xs-12')[1]
    except IndexError:
        print("First or last chapter")
        next_link = soup.find_all('a', class_='btn btn-primary col-xs-12')[0]
        if next_link.text.strip() == "Previous Chapter":
            return None

    try:
        return "https://royalroad.com" + next_link['href']
    except IndexError:
        print("no more chaps")
        return None


async def get_first_chapter_url(story_url):
    html = await get(story_url)
    soup = BeautifulSoup(html, 'html.parser')
    first_chapter = soup.find('a', class_='btn btn-lg btn-primary')
    return "https://royalroad.com" + first_chapter['href']


async def get_metadata(story_url):
    html = await get(story_url)
    soup = BeautifulSoup(html, 'html.parser')
    author = soup.find('h4', property='author').text
    description = soup.find('div', class_='description').text
    cover_url = soup.find('img', class_='thumbnail inline-block')['src']
    title = soup.find('h1', property='name').text
    return [author, description, cover_url, title]


async def file_writer(chapter_url, file, ending):
    async with aiofiles.open(file+ending, "a+", encoding="utf-8") as f:
        text, note, title = await get_chapter_text(chapter_url)
        await f.write(title)
        if note is not None:
            await f.write(note)
        await f.write(text)


async def get_whole_story(story_url, file_name, mode="md"):
    next_url = await get_first_chapter_url(story_url)
    while next_url is not None:
        if mode == "md":
            await file_writer(next_url, file_name, ".md")
        elif mode == "mobi":
            await file_writer(next_url, file_name, ".html")
        next_url = await get_next_chapter_url(next_url)


async def convert_to_mobi(path, file, metadata):
    title, author, cover, description = metadata[3], metadata[0], metadata[2], metadata[1]
    subprocess.run(["C:\\Program Files\\Calibre2\\ebook-convert.exe",
                    path+"\\"+file+".html",
                    path+"\\"+file+".mobi",
                    "--title="+title,
                    "--authors="+author,
                    "--cover="+cover,
                    "--comments="+description
                    ],
                   shell=True)


async def main(story_url, path):
    # await get_whole_story(story_url, path, mode="mobi")
    p = path.split("\\")
    path, file = "\\".join(p[:-1]), p[-1]
    await convert_to_mobi(path, file, metadata=await get_metadata(story_url))


asyncio.run(main(
    "https://www.royalroad.com/fiction/54810/system-error-litrpg-reincarnation-ft-copious-amounts",
    "C:\\Users\\Tom-User\\Downloads\\Royal_road_downloads\\blue_boxes"
))
