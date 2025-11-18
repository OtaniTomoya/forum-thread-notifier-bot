# Forum Thread Notifier Bot

Discord フォーラムチャンネルに新しくスレッドが立った瞬間、指定した一般チャンネルへ通知する Python 製 Bot。

## 必要条件
- Python 3.10 以上
- Discord アプリケーションに登録済みの Bot トークン
- `discord.py`, `python-dotenv` 

```bash
pip install -U discord.py python-dotenv
```

## 環境変数
`.env` などで以下を設定してください。

```
DISCORD_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
FORUM_CHANNEL_IDS=111111111111111111,222222222222222222
ANNOUNCE_CHANNEL_ID=333333333333333333
```

- `FORUM_CHANNEL_IDS` : 監視したいフォーラムチャンネル ID をカンマ区切りで列挙
- `ANNOUNCE_CHANNEL_ID` : 通知を送りたい一般チャンネル ID

## 起動方法
```bash
python bot.py
```
