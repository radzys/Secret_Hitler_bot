import os
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import vk_api
import sys

class Gamer:
    def __init__(self, from_id, conversation_peer):
        self.from_id = from_id
        self.peer_id = conversation_peer
        main_dir = sys.path[0]
        print(main_dir)
        token = os.path.join(main_dir, 'token.txt')
        with open(token, 'r') as tk:
            api_token = tk.read()
        vk_ses = vk_api.VkApi(token=api_token)
        user_info = vk_ses.method('users.get', {'fields': 'first_name, last_name, domain', 'user_id': self.from_id})[0]
        self.first_name = user_info.get("first_name")
        self.last_name = user_info.get("last_name")
        self.name = f'{self.first_name} {self.last_name}'
        # self.name = f'name{self.from_id}'
        self.is_chancellor = False
        self.is_president = False
        self.was_chancellor = False
        self.was_president = False
        self.alive = True
        self.loyalty_checked = False


