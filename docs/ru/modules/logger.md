## Logger

Модуль для логгирования каких либо сообщений.

### Класс

keep=True: будет использован файл для текущего сеанса приложения, с добавления времени запуска

keep=False: будет использован файл для текущей даты

#### log(message=,section=,name=,noConsole=)

Сохраняет строку в файл в формате [time] [$name] [$section] $message

message = сообщение, которые ты хочешь передать

section = секция, в которой произошло событие (например, AsyncDownloader)

name = тип сообщения ("success", "message", "error")

noConsole = При False не отображает сообщение в консоли

#### logException(input_exception=,section=,noConsole=)

Алиас для log(). Сохраняет текст исключения.
