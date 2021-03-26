import asyncio
from enum import Enum
from contextlib import asynccontextmanager
from time import monotonic
import logging

import pymorphy2
import aiohttp
import pytest
from aiohttp.client_exceptions import ClientError, InvalidURL
from async_timeout import timeout

from adapters import inosmi_ru, exceptions
from text_tools import split_by_words, calculate_jaundice_rate
from constants import ASYNC_TIMEOUT


logger = logging.getLogger('basic_logger')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


@asynccontextmanager
async def process_timer():
    """Контекстный менеджер для замера времени анализа статьи."""
    start_time = monotonic()
    try:
        yield
    finally:
        end_time = monotonic() - start_time
        logger.info(f"Анализ закончен за {end_time} сек.")


def load_dict(path_to_dict):
    """Загрузка словаря 'заряженных' слов."""
    with open(path_to_dict, encoding='utf8') as fh:
        words = fh.read().splitlines()
    return words


async def fetch(session, url):
    """Загрузка статьи."""
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url, results, max_timeout=ASYNC_TIMEOUT):
    """Анализ статьи на 'желтушность."""
    async with process_timer():
        score = None
        words_count = None
        try:
            async with timeout(max_timeout):
                html = await fetch(session, url)
            status = ProcessingStatus.OK
            article = inosmi_ru.sanitize(html)
            async with timeout(max_timeout):
                words = split_by_words(morph, article)
                score = calculate_jaundice_rate(words, charged_words)
            words_count = len(words)
        except (ClientError, InvalidURL):
            status = ProcessingStatus.FETCH_ERROR
            url = 'Url not exist'
        except exceptions.ArticleNotFound:
            status = ProcessingStatus.PARSING_ERROR
        except asyncio.exceptions.TimeoutError:
            status = ProcessingStatus.TIMEOUT

        results.append({
            'status': status.value,
            'url': url,
            'rating': score,
            'words_count': words_count
        })


@pytest.fixture()
async def session():
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture()
async def morph():
    morph = pymorphy2.MorphAnalyzer()
    yield morph


@pytest.mark.asyncio
async def test_process_article(session, morph):
    results = []
    WRONG_URL = 'https:/ria.ru/20210314/zolotarev-1601149637.html'
    NO_ADAPTER_URL = 'https://ria.ru/20210314/zolotarev-1601149637.html'
    CORRECT_URL = 'https://inosmi.ru/politic/20210311/249309407.html'

    charged_words = load_dict('charged_dict/negative_words.txt')

    await process_article(session, morph, charged_words, WRONG_URL, results)
    assert results[0]['status'] == 'FETCH_ERROR'

    await process_article(session, morph, charged_words, NO_ADAPTER_URL, results)
    assert results[1]['status'] == 'PARSING_ERROR'

    await process_article(session, morph, charged_words,
                          CORRECT_URL,
                          results,
                          max_timeout=0)
    assert results[2]['status'] == 'TIMEOUT'

