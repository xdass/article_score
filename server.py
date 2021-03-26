from aiohttp import web
import aiohttp
import pymorphy2
from anyio import create_task_group

from article import process_article, load_dict
from constants import MAX_URLS


async def collect(urls, morph, charged_words):
    """Анализ списка статей."""
    results = []
    async with aiohttp.ClientSession() as session:
        async with create_task_group() as tg:
            for url in urls:
                await tg.spawn(process_article, session, morph, charged_words, url, results)
    return results


async def handle(request, morph, charged_words, max_articles):
    """Обработчик http запроса."""
    query_params = dict(request.query)
    if not query_params:
        return web.json_response({'error': 'url parameter not provided'})
    urls = query_params['urls'].split(',')
    if len(urls) > max_articles:
        return web.json_response({"error": "too many urls in request, should be 10 or less"}, status=400)
    results = await collect(urls, morph, charged_words)
    return web.json_response({'urls': results})


if __name__ == '__main__':
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_dict('charged_dict/negative_words.txt')
    app = web.Application()
    app.add_routes([web.get('/', lambda request=web.Request: handle(request, morph, charged_words, MAX_URLS))])
    web.run_app(app)
