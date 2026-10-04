[<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/head.svg">](https://github.com/lowfc/boosty_downloader/releases)

![GitHub stars](https://img.shields.io/github/stars/lowfc/boosty_downloader?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/lowfc/boosty_downloader?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&style=flat-square)
![Latest Release](https://img.shields.io/github/v/release/lowfc/boosty_downloader?style=flat-square)

---

Application for downloading content from boosty.to

## 👀 Demo

<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/demo_1.1.gif" alt="">

You can download content available to you according to your subscription level. 
To download restricted content, please log in.

By using the application, you agree to the <a href="https://github.com/lowfc/boosty_downloader/blob/develop/LICENSE.md">user agreement</a>.

## 🪄 Features

#### Download methods

- 🔗 Download post by link
- 📆 Download posts with a filter by publication date
- ✉️ Download image by link, including from personal messages

#### Supported content types

- 🖼️ Photos
- 📽️ Videos
- 🎧 Audios
- 📂 Attached files
- 📝 Post text and header

#### Supported operating systems

- ✅ Windows
- ✅ macOS
- ✅ Linux

#### Authorization ability

Authorize app to get available for you private content:

<img src="https://raw.githubusercontent.com/lowfc/static-repo/refs/heads/main/boosty_downloader/demo_2.0.gif" alt="">

## 💻 Installation

1. Go to [latest release](https://github.com/lowfc/boosty_downloader/releases/latest);
2. Download the archive for your operating system;
3. Unzip the archive to any folder;
4. Run the app.

⚠️ **Windows**: The path to this folder must contain only latin characters. Make sure that the folder path does not contain cyrillic or other prohibited characters.

⚠️ **macOS**: When attempting to launch the app, you may encounter a warning from the operating system about launching an app from an unknown developer. 
To open the app anyway, read official instruction (these steps only need to be performed once): https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/mac

📟 **CLI**: If you want to use the CLI version of this app, it is maintained in this repository: https://github.com/Banana-P0wer/Cli-Banana-BoostyDownloader

## 🐍 Development

### Localization

The interface supports English and Russian. On first launch, the app uses the
device's primary language, falling back to English if it is not supported.
Choose a language in **Settings → General → Language** to apply it immediately
without restarting. The saved choice takes precedence on later launches.

Settings save automatically: switches, lists, themes, and folder selections save
immediately; text fields save two seconds after the last edit. Valid pending
values are also saved before leaving Settings. Invalid numbers remain highlighted
and do not block other settings. A failed save can be retried from the status row.

UI catalogs live in `src/locales/en.json` and `src/locales/ru.json`. English source
messages are translation keys; use `localizer.t(message, **values)` for named
placeholders and `localizer.plural(key, count)` for counts. Add a catalog and a
native language name to `SUPPORTED_LANGUAGES` in `src/localization.py` to add a
language. Configure Flet's built-in controls through `LocaleConfiguration`; keep
original post titles, paths, and diagnostic logs intact.

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
