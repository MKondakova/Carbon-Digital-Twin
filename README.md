# MVP ПО для ЦД ПАН-УВ
## Содержание репозитория
- [Модуль считывания информации с датчиков](sensors_module/)
- [Модуль хранения данных](data_storage/)
- ...
## Принцип работы
Данные попадают в цифровой двойник из модуля считывания данных с датчиков, а также из модуля диагностики.
После они сохраняются в базу данных (MySQL). Оттуда из запрашивает модуль предсказания свойств волокна.

