# Boosty media downloader (windows)

This script download all **AVAILABLE FOR YOU** media from boosty.to page


## Create venv:
```shell
python3 -m venv .\venv
```

## Activate venv:
```shell
.\venv\Scripts\activate
```

## Install requirements:
```shell
pip install -r requirements.txt
```

## Set-up:
1. Open .\core\config.py
2. Type creater name to creator_name
3. Type download destination dir to sync_dir

> You can download free content without authorization, but if you want download private 
> content that you have access to fill the cookie and authorization fields. You can get it in
> browser net tools, inspecting any api request. <br>
> **!!! Do not pass the values of these fields to anyone**

## Here we go

```shell
python main.py
```