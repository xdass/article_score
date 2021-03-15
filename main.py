import aiohttp
import asyncio
from enum import Enum
from aiohttp.client_exceptions import InvalidURL
from contextlib import contextmanager, asynccontextmanager
from time import monotonic
import logging

from adapters import inosmi_ru, exceptions
from text_tools import split_by_words, calculate_jaundice_rate
from anyio import create_task_group
from async_timeout import timeout
import pymorphy2


logger = logging.getLogger('basic_logger')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)


TEST_ARTICLES = {
    'Тестовая':
        'https://ria.ru/20210314/zolotarev-1601149637.html',
    'В Японии бурно комментируют заявления Лаврова по размещению американских ракет':
        'https://inosmi.ru/politic/20210314/249326677.html',
    'Teologia Polityczna (Польша): «Северный поток» как лакмусовая бумажка политической действительности':
        'https://inosmi.ru/politic/20210311/249309407.html',
    'The Economist (Великобритания): теплые воды Арктики могут изменить расклад на рынке сжиженного природного газа':
        'https://inosmi.ru/economic/20210313/249325943.html',
    'Байден calling: когда Зеленский дождется звонка из Вашингтона (Апостроф, Украина)':
        'https://inosmi.ru/politic/20210313/249326007.html',
    'Клебо сломался еще до того, как его укатал Большунов: «Просто ужасно» (NRK, Норвегия)':
        'https://inosmi.ru/social/20210314/249326951.html'
}


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


@asynccontextmanager
async def counter():
    start_time = monotonic()
    yield
    end_time = monotonic() - start_time
    logger.info(f"Анализ закончен за {end_time} сек.")


async def fetch(session, url):
    async with timeout(10):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()


async def process_article(session, morph, charged_words, url, title, results):
    async with counter():
        score = None
        words_count = None
        try:
            html = await fetch(session, url)
            status = ProcessingStatus.OK
            article = inosmi_ru.sanitize(html)
            words = split_by_words(morph, article)
            score = calculate_jaundice_rate(words, charged_words)
            words_count = len(words)
        except InvalidURL:
            status = ProcessingStatus.FETCH_ERROR
            title = 'Url not exist'
        except exceptions.ArticleNotFound:
            status = ProcessingStatus.PARSING_ERROR
        except asyncio.exceptions.TimeoutError:
            status = ProcessingStatus.TIMEOUT

        print('Заголовок:', title)
        print('Статус:', status)
        print('Рейтинг:', score)
        print('Слов в статье:', words_count)
        print('\n')
        # results.append({
        #     'status': status.value,
        #     'title': title,
        #     'rating': score,
        #     'words_count': words_count
        # })


async def main():
    morph = pymorphy2.MorphAnalyzer()
    # TODO вынести в ф-цию загрузку словаря
    with open('charged_dict/negative_words.txt', encoding='utf8') as fh:
        charged_words = fh.read().splitlines()

    results = []
    # with open('gogol_nikolay_taras_bulba.txt', encoding='utf8') as fh:
    #     article = fh.read()
    # with counter():
    #     words = split_by_words(morph, article)
    #     score = calculate_jaundice_rate(words, charged_words)
    #     words_count = len(words)
    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for title, url in TEST_ARTICLES.items():
                await tg.spawn(process_article, session, morph, charged_words, url, title, results)

    # # TODO вынести в ф-цию
    # for result in results:
    #     print('Заголовок:', result['title'])
    #     print('Статус:', result['status'])
    #     print('Рейтинг:', result['rating'])
    #     print('Слов в статье:', result['words_count'])
    #     print('\n')


asyncio.get_event_loop().run_until_complete(main())
# asyncio.run(main())
