from typing import List, Union, Set

from discord.ext import commands
import discord
from pprint import pprint


class ReactionManager:
    """リアクションを監視するメッセージとそのレスポンスの管理クラス

    Attributes
    -----------
    manage_message: :class:`discord.Message`
        リアクションを管理するメッセージクラス
    send_message:   :class:`discord.Message`
        リアクション数を送った後変更できるように、送ったメッセージ情報を管理するクラス
    """
    __slots__ = ('manage_message', 'send_message')

    def __init__(self, message: discord.Message):
        self.manage_message = message
        self.send_message: Union[discord.Message, None] = None


class UserReaction:
    """リアクションの絵文字と、リアクションしたユーザを取得するクラス

    Attributes
    -----------
    reaction:  :class:`discord.Reaction`
        該当するリアクション情報
    user_list: :class:`List[discord.User]`
        リアクションをしたユーザ
    """
    __slots__ = ('reaction', 'user_list')

    def __init__(self, reaction: discord.Reaction):
        self.reaction = reaction
        self.user_list: List[discord.User] = []


class ManageReactionCog(commands.Cog):
    """リアクション回数管理クラス（凸数管理用）

    Attributes
    -----------
    bot         :class:`discord.ext.commands.Bot`
        botのクライアント情報
    management: :class:`List[ReactionManager]`
        管理対象になるリアクションマネージャ
    """
    __slots__ = ('bot', 'management')

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.management: List[ReactionManager] = []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """メッセージを受信したときに動くイベント
        自分に対してメンションが発生した際、該当のメッセージを管理対象に追加する

        Parameters
        ----------
        message : :class:`discord.Message`
            送信されたメッセージの内容

        Returns
        -------
        """
        if message.author == self.bot.user:
            return
        if self.bot.user not in message.mentions:
            return

        reaction_manager: ReactionManager = ReactionManager(message)
        self.management.append(reaction_manager)
        print("管理先に追加したよ！")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """何かにリアクションが追加されたときに実行される。
        本クラスで管理しているメッセージに対してリアクションが発生した場合は、
        そのメッセージについているリアクションを集計して、メッセージを送信する。
        すでに送信済みの場合は編集する。

        Parameters
        ----------
        payload:  :class:`discord.RawReactionActionEvent`
            該当のリアクション内容

        Returns
        -------

        """

        # reactionをつけたものが管理対象の場合にのみ動作する
        message_manager: Union[ReactionManager, None] = None
        for reaction_manager in self.management:
            if payload.message_id == reaction_manager.manage_message.id:
                message_manager = reaction_manager
        if message_manager is None:
            return

        # 自分がリアクションした場合はスルー
        if payload.user_id == message_manager.manage_message.guild.me.id:
            return

        # 該当のものにはリアクションを追加する
        await message_manager.manage_message.add_reaction(payload.emoji)

        # メッセージを更新してreactionの一覧を取得する
        user_reactions: List[UserReaction] = await self.get_reaction_user(message_manager)
        # ユーザの一覧を取得
        mention_users: List[discord.abc.User] = await self.get_mention_users(message_manager.manage_message)
        pprint(mention_users)

        # 表示用メッセージの生成
        resp_str: str = self.create_response(user_reactions, mention_users)

        # メッセージをまだ送信してないならメッセージを作って送信する
        if message_manager.send_message is None:
            message_manager.send_message = await message_manager.manage_message.channel.send(resp_str)
        else:
            await message_manager.send_message.edit(content=resp_str)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """何かからリアクションが削除されたときに実行される。
        動作は on_raw_reaction_add() と同じ

        Parameters
        ----------
        payload:  :class:`discord.RawReactionActionEvent`
            該当のリアクション内容

        Returns
        -------

        """
        await self.on_raw_reaction_add(payload)

    async def get_reaction_user(self, reaction_manager: ReactionManager) -> List[UserReaction]:
        """管理対象のメッセージに対して、一人当たり何回リアクションしたか取得する

        Parameters
        ----------
        reaction_manager: :class:`ReactionManager`
            管理対象のメッセージ

        Returns
        -------
        List[UserReaction]
            リアクションとそのリアクションをしたユーザの情報を取得する
        """
        # 更新する
        channel: discord.TextChannel = self.bot.get_channel(reaction_manager.manage_message.channel.id)
        reaction_manager.manage_message = await channel.fetch_message(reaction_manager.manage_message.id)

        # reactionを取得
        reactions: List[discord.Reaction] = reaction_manager.manage_message.reactions

        # reactionをしたユーザを取得
        resp: List[UserReaction] = []
        for reaction in reactions:
            r = UserReaction(reaction)
            async for user in reaction.users():
                # botのリアクションはスルー
                if user.bot:
                    continue
                r.user_list.append(user)
            resp.append(r)

        return resp

    @staticmethod
    def create_response(user_reactions: List[UserReaction], all_user: List[discord.abc.User]) -> str:
        """レスポンス表示用の出力を作る関数

        Parameters
        ----------
        user_reactions: :class:`List[UserReaction]`
            リアクションをした人のリスト
        all_user:       :class:`List[discord.abc.User]`
            対象のユーザ全員

        Returns
        -------
        :class:`str` チャットに返答するレスポンス

        """
        return_str: str = ""

        # userごとに出す
        user_dict = {}
        for user_reaction in user_reactions:
            for user in user_reaction.user_list:
                if user.name not in user_dict.keys():
                    user_dict[user.name] = 0
                user_dict[user.name] += 1

        for i in range(len(user_reactions) + 1):
            s = "反応数{} ``` {} ```\n"
            # ノーリアクションは特殊処理
            if i == 0:
                reaction_user_name: Set[str] = set(user_dict.keys())
                all_user_name: Set[str] = set(map(lambda x: x.name, all_user))
                s = s.format(i, ' '.join(all_user_name - reaction_user_name))
            else:
                d = {k: v for k, v in user_dict.items() if v == i}
                s = s.format(i, ' '.join(d.keys()))
            return_str += s

        return return_str

    #@staticmethod
    async def get_mention_users(self, message: discord.Message) -> List[discord.abc.User]:
        """メンションしているユーザをすべて取得する

        Parameters
        ----------
        message: :class:`discord.Message`
            対象のメッセージ

        Returns
        -------
        :class:`List[discord.abc.User]`
            メンションされたユーザのリスト
        """
        # everyone指定の際は、そのチャンネルにいるメンバー全員
        if message.mention_everyone:
            guild: discord.Guild = message.guild
            members: List[discord.Member] = guild.members
            return list(filter(lambda x: x.id != guild.me.id, members))

        # その他の場合は個別にメンションを集める
        resp: List[discord.abc.User] = []
        # 直メンションしたユーザを取得する
        mentions_users: List[discord.abc.User] = list(filter(lambda x: x.id != message.guild.me.id, message.mentions))

        # ロールメンションした場合、そのロールのメンバを取得する
        role_mention_users: List[discord.Member] = []
        role_mentions: List[discord.Role] = message.role_mentions
        print("role mention")
        pprint((await self.bot.fetch_guild(message.guild.id)).get_role(role_mentions[0].id).members)
        for role_mention in role_mentions:
            role_mention_users.extend(role_mention.members)
            print("role members")
            pprint(role_mention.members)

        for mention_user in mentions_users:
            if len(list(filter(lambda x: x.id == mention_user.id, resp))) == 0:
                resp.append(mention_user)
                pprint(mention_user)

        for role_mention_user in role_mention_users:
            if len(list(filter(lambda x: x.id == role_mention_user.id, resp))) == 0:
                resp.append(role_mention_user)
                pprint(role_mention_user)

        return list(filter(lambda x: x.id != message.guild.me.id, resp))
