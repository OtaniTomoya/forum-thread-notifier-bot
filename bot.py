"""Discord forum thread notifier bot.
このモジュールは指定フォーラムに新規スレッドが立った瞬間に一般チャンネルへ通知します。"""

from __future__ import annotations

import logging
import os
from typing import Final, Sequence

import discord
from dotenv import load_dotenv

# ====== ロギング初期化 ======
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("forum_thread_notifier")

# .env を読み込んで環境変数をプロセスに取り込む。
load_dotenv()


def build_intents() -> discord.Intents:
    """フォーラムスレッド検知に必要な最小限の Intents を返します。"""
    intents = discord.Intents.none()
    intents.guilds = True  # スレッドイベントに必須なので唯一明示的に有効化する。

    return intents


def format_notification(thread: discord.Thread) -> str:
    """一般チャンネルへ送る通知文面を構築します。"""
    thread_url = f"https://discord.com/channels/{thread.guild.id}/{thread.id}"
    thread_owner = f"<@{thread.owner_id}>" if thread.owner_id else "不明な作成者"

    return (
        "**新しいスレッドが作成されました**\n"
        f"{thread.name}"
        f"{thread_owner}\n"
        f"{thread_url}"
    )


def ensure_token() -> str:
    """環境変数から Bot トークンを取得し、存在しなければエラーを投げます。"""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("環境変数 DISCORD_BOT_TOKEN が設定されていません。")
    return token


def parse_forum_channel_ids(raw_ids: str) -> list[int]:
    """
    監視対象フォーラムID文字列をカンマ区切りでパースして整数リストに変換する。

    各種チャンネルIDは Discord 側仕様で 64bit 整数なので int 変換で十分。
    """
    ids: list[int] = []
    for chunk in raw_ids.split(","):
        stripped = chunk.strip()
        if not stripped:
            continue
        try:
            ids.append(int(stripped))
        except ValueError as exc:  # ID 文字列以外が混ざっていた場合は早期に知らせる。
            raise ValueError(f"FORUM_CHANNEL_IDS に数値以外の値 '{stripped}' が含まれています。") from exc
    if not ids:
        raise ValueError("FORUM_CHANNEL_IDS に有効なIDが一つもありません。")
    return ids


def load_channel_settings() -> tuple[list[int], int]:
    """フォーラムID一覧と通知チャンネルIDを環境変数から取得し、整形した上で返す。"""
    forum_ids_raw = os.getenv("FORUM_CHANNEL_IDS")
    if not forum_ids_raw:
        raise RuntimeError("環境変数 FORUM_CHANNEL_IDS が設定されていません。カンマ区切りで指定してください。")
    forum_ids = parse_forum_channel_ids(forum_ids_raw)

    announce_channel_raw = os.getenv("ANNOUNCE_CHANNEL_ID")
    if not announce_channel_raw:
        raise RuntimeError("環境変数 ANNOUNCE_CHANNEL_ID が設定されていません。")
    try:
        announce_channel_id = int(announce_channel_raw)
    except ValueError as exc:
        raise ValueError("ANNOUNCE_CHANNEL_ID には数値チャンネルIDを設定してください。") from exc

    return forum_ids, announce_channel_id


class ForumThreadNotifier(discord.Client):
    """フォーラム新規スレッドを監視して通知するシンプルな Client 実装。"""

    def __init__(
        self,
        *,
        intents: discord.Intents,
        forum_channel_ids: Sequence[int],
        announce_channel_id: int,
    ) -> None:
        super().__init__(intents=intents)
        # set で保持することで membership チェックを高速化。
        self._forum_channel_ids: Final[frozenset[int]] = frozenset(forum_channel_ids)
        self._announce_channel_id: Final[int] = announce_channel_id

    async def on_ready(self) -> None:  # noqa: D401
        """Discord ログイン成功をログに吐き、Bot 名も表示する。"""
        logger.info("Bot logged in as %s (id=%s)", self.user, getattr(self.user, "id", "unknown"))

    async def on_thread_create(self, thread: discord.Thread) -> None:
        """新規スレッド作成イベントを受け取り、対象フォーラムなら通知を行う。"""
        if thread.parent_id not in self._forum_channel_ids:
            logger.debug(
                "Ignore thread %s (id=%s) because parent %s is not monitored",
                thread.name,
                thread.id,
                thread.parent_id,
            )
            return

        announce_channel = thread.guild.get_channel(self._announce_channel_id)
        if announce_channel is None:
            logger.error(
                "Announce channel %s が取得できません。権限やIDを確認してください。",
                self._announce_channel_id,
            )
            return

        message = format_notification(thread)
        await announce_channel.send(message)
        logger.info(
            "Notified new thread '%s' (id=%s) in parent %s",
            thread.name,
            thread.id,
            thread.parent_id,
        )


def main() -> None:
    """Bot の起動エントリポイント。"""
    token = ensure_token()
    forum_channel_ids, announce_channel_id = load_channel_settings()
    intents = build_intents()
    client = ForumThreadNotifier(
        intents=intents,
        forum_channel_ids=forum_channel_ids,
        announce_channel_id=announce_channel_id,
    )

    logger.info("Starting bot with monitored forums: %s", forum_channel_ids)
    client.run(token)


if __name__ == "__main__":
    main()
