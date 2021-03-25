# Фильтр желтушных новостей

Сервис для проверки новостей на "желтушность".
Взаимодействие с сервисом осуществляется через API-запросы

Пока поддерживается только один новостной сайт - [ИНОСМИ.РУ](https://inosmi.ru/). Для него разработан специальный адаптер, умеющий выделять текст статьи на фоне остальной HTML разметки. Для других новостных сайтов потребуются новые адаптеры, все они будут находиться в каталоге `adapters`. Туда же помещен код для сайта ИНОСМИ.РУ: `adapters/inosmi_ru.py`.

В перспективе можно создать универсальный адаптер, подходящий для всех сайтов, но его разработка будет сложной и потребует дополнительных времени и сил.

# Как установить

Вам понадобится Python версии 3.7 или старше. Для установки пакетов рекомендуется создать виртуальное окружение.

Первым шагом установите пакеты:

```python3
pip install -r requirements.txt
```

# Как запустить

```python3
python server.py

======== Running on http://0.0.0.0:8080 ========
(Press CTRL+C to quit)
```
## Настройка
В файле `constants.py` хранятся следующие настройки:
- MAX_URLS максимальное количество обрабатываемых статей (по умолчанию 5 шт.)
- ASYNC_TIMEOUT время обработки статьи (по умолчанию 10 сек.)


# Пример
## Запрос на анализ статей
```
http://127.0.0.1:8080/?urls=http://inosmi.ru/politic/20210314/249326677.html,https://inosmi.ru/politic/20210311/249309407.html,https://ria.ru/20210314/zolotarev-1601149637.html
```

## Результат
```json
{
  "urls": [
      {
      "status": "OK",
      "url": "https://inosmi.ru/politic/20210311/249309407.html",
      "rating": 0.29,
      "words_count": 698
      },
      {
      "status": "PARSING_ERROR",
      "url": "https://ria.ru/20210314/zolotarev-1601149637.html",
      "rating": null,
      "words_count": null
      },
      {
      "status": "OK",
      "url": "http://inosmi.ru/politic/20210314/249326677.html",
      "rating": 0.41,
      "words_count": 1220
      }
  ]
}
```

# Как запустить тесты

Для тестирования используется [pytest](https://docs.pytest.org/en/latest/), тестами покрыты фрагменты кода сложные в отладке: text_tools.py и адаптеры. Команды для запуска тестов:

```
python -m pytest adapters/inosmi_ru.py
```

```
python -m pytest text_tools.py
```

```
python -m pytest article.py
```

# Цели проекта

Код написан в учебных целях.
