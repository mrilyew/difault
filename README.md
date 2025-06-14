## Prethmeta

App for content saving with flexible settings

Look at [docs](docs/ru/README.md)

## Задачи:

### Экзекьютеблы

- [ ] Pre-execute если ничего не передано (?)
- [ ] Хуки выполнения
- [ ] Cli only use акты
- [ ] Кэширование списка экзекьютеблов и тамбнейлов
- [x] Разделить Executable на Runnable, Documentable, Saveable, RecursiveDeclarable

### Экспорт

- [ ] Acts.Metamorphosis.Export (to .th zip)
- [ ] Acts.Metamorphosis.Import
- [ ] Acts.Metamorphosis.CopyToDirectory
- [ ] Подмена даты создания файла при экспорте (если возможно?)

### Метаданные

- [ ] Акты для каждого mime типа

### Contentunit

- [ ] Генерируемая колонка indexation_content_string (колонка `content` без ключей и пробелов)
- [x] Переписать превью
- [ ] Замена ID на UUID или что то типо того
- [ ] Подключение альтернативной базы данных

### Репрезентации

- [x] Разделить representation и strategy
- [ ] Post-execute действия (?)
- [ ] file_containment (?)

### Инциализация

- [ ] Адаптация под bash и powershell

### Веб кравлер

- [ ] Переписать
- [ ] Режим archive.is без сохранения скриптов
- [ ] Определённые декларируемые функции для определённого сайта

### Acts.ContentUnits.

- [ ] Search
- [ ] Remove
- [ ] GetById
- [ ] Edit
- [ ] ReorderGlobal
- [ ] Link
- [ ] Unlink
- [ ] GetLinks

### Acts.Executables.

- [ ] List

### Acts.Storage.

- [ ] ClearTemp

### ContentUnitRelation

- [ ] .is_revision
