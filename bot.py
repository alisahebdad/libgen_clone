import bs4 
from abc import ABC,abstractmethod
import logging
import asyncio
import aiohttp
import urllib
import random

class Task(ABC):
    def __init__(self,name:str) -> None:
        self._data = {}
        self._name = name

    def set(self,key:str,value):
        self._data[key] = value

    @abstractmethod
    async def run(self):
        raise NotImplementedError()


class SearchTask(Task):
    def __init__(self) -> None:
        super().__init__(name='SearchTask')
    @staticmethod
    def makeUrl(search:str,page:int=1) -> str:
        search = search.split()
        if len(search) == 0:
            raise Exception('bad input')
        search_text = search[0]
        for i in range(1,len(search)):
            search_text = search_text + '+' + search[i]
        pattern = f'https://libgen.is/search.php?&req={search_text}&phrase=1&view=simple&column=def&sort=def&sortmode=ASC&page={page}'
        return pattern

    async def getPDFLink(self,addr):
        
        print ('pdf',addr)

    async def getMoreInfo(self,addr):
        url = f'http://libgen.is/{addr}'
        output = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = bs4.BeautifulSoup(html,'html.parser')
                for img in soup.find_all('img'):
                    output['cover'] = f"http://libgen.is{img['src']}"
                for tr in soup.find_all('tr'):
                    if 'ISBN' in tr.text:
                        output['ISBN'] = [s.strip() for s in tr.find_all('td')[1].text.split(',')]
        return output

    async def run(self):
        if 'searchPhrase' not in self._data:
            raise Exception(f'searchPhrase is\'t set')
        url = SearchTask.makeUrl(self._data['searchPhrase'])
        logging.debug(f'url is {url}')
        more_q = []
        output = []
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if 'html' in self._data:
                    html = await response.text()
                    with open (self._data['html'],'w') as file:
                        file.write(html)
                    soup = bs4.BeautifulSoup(html,'html.parser')
                    for row in soup.find_all('tr'):
                        parsed_row = row.find_all('td')
                        book = {}
                        if len(parsed_row) == 12:
                            book['id'] = parsed_row[0].text
                            book['publisher'] = parsed_row[3].text
                            book['year'] = parsed_row[4].text
                            book['pages'] = parsed_row[5].text
                            book['language'] = parsed_row[6].text
                            book['size'] = parsed_row[7].text
                            book['format'] = parsed_row[8].text
                            book['authors'] = []
                            for author in parsed_row[1].find_all('a'):
                                book['authors'].append(author.text)
                            book['title'] = parsed_row[2].find_all('a',recursive=False)[0].text
                            more_q.append(self.getMoreInfo(parsed_row[2].find_all('a')[0]['href']))
                            output.append(book)
        result = await asyncio.gather(*more_q)
        for i in range(len(output)):
            for item in result[i]:
                output[i][item] = result[i][item]
        print (output)


class Scrapper:
    TARGET = 'http://libgen.is'
    def __init__(self) -> None:
        pass
    async def search(self,text:str):
        t1 = SearchTask()
        t1.set('searchPhrase',text)
        t1.set('html','1.html')
        await t1.run()


async def main():
    myScrapper = Scrapper()
    await myScrapper.search('clean code')


if __name__ == '__main__':
    asyncio.run(main())

        