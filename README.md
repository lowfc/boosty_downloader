[<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/head.svg">](https://github.com/lowfc/boosty_downloader/releases)

![Звёзды на GitHub](https://img.shields.io/github/stars/lowfc/boosty_downloader?style=flat-square)
![Открытые задачи на GitHub](https://img.shields.io/github/issues/lowfc/boosty_downloader?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&style=flat-square)
![Последний релиз](https://img.shields.io/github/v/release/lowfc/boosty_downloader?style=flat-square)

---

Приложение для скачивания контента с boosty.to

Русский | [English](README.en.md)

## 👀 Демо

<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/demo-1.webp" alt="">

Вы можете скачивать контент, доступный вам в рамках вашего уровня подписки.
Для скачивания контента с ограниченным доступом войдите в аккаунт.

Используя приложение, вы соглашаетесь с <a href="https://github.com/lowfc/boosty_downloader/blob/develop/LICENSE.md">пользовательским соглашением</a>.

## 🪄 Возможности

#### Способы скачивания

- 🔗 Скачивание поста по ссылке
- 📆 Скачивание постов с фильтром по дате публикации
- ✉️ Скачивание изображения по ссылке, в том числе из личных сообщений

#### Поддерживаемые типы контента

- 🖼️ Фото
- 📽️ Видео
- 🎧 Аудио
- 📂 Прикреплённые файлы
- 📝 Текст и заголовок поста

#### Поддерживаемые операционные системы

- ✅ Windows
- ✅ macOS
- ✅ Linux

#### Авторизация

Войдите в аккаунт в приложении, чтобы скачивать доступный вам закрытый контент:

<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/demo-auth-1.webp" alt="">

## 💻 Установка

1. Перейдите на страницу [последнего релиза](https://github.com/lowfc/boosty_downloader/releases/latest);
2. Скачайте архив для вашей операционной системы;
3. Распакуйте архив в любую папку;
4. Запустите приложение.

⚠️ **Windows**: Путь к этой папке должен содержать только латинские символы. Убедитесь, что в пути нет кириллицы или других недопустимых символов.

⚠️ **macOS**: При запуске приложения операционная система может показать предупреждение о неизвестном разработчике.
Чтобы открыть приложение, следуйте официальной инструкции (эти действия нужно выполнить только один раз): https://support.apple.com/ru-ru/guide/mac-help/mh40616/mac

📟 **CLI**: Версия приложения для командной строки поддерживается в этом репозитории: https://github.com/Banana-P0wer/Cli-Banana-BoostyDownloader

## 🐍 Development

### Run the app

Run as a desktop app:

```
uv run flet run
```

Run as a web app:

```
uv run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://docs.flet.dev/).

### Build the app

**Android**

```
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://docs.flet.dev/publish/android/).

**iOS**

```
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://docs.flet.dev/publish/ios/).

**macOS**

```
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://docs.flet.dev/publish/macos/).

**Linux**

```
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://docs.flet.dev/publish/linux/).

**Windows**

```
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://docs.flet.dev/publish/windows/).
