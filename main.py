import random
from event import Event
from game import Game
import sys
import time
import os
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import vk_api

REGIME = 'PROD'
MESSAGE_EVENT = 'NEW_MESSAGE'


def get_game(peer_id, games):
    for game in games:
        if peer_id == game.peer_id:
            return game
    game = Game(peer_id)
    games.append(game)
    return game


def processing(event, games):
    if event.from_id == event.peer_id:
        for game_1 in games:
            for gamer in game_1.gamers_list:
                if gamer.from_id == event.from_id:
                    game = get_game(game_1.peer_id, games)
                    game.receive_message(event)
    else:
        game = get_game(event.peer_id, games)
        game.receive_message(event)


def main(regime):
    with open('log.txt', 'w'):
        pass
    games = []
    if regime == 'PROD':

        main_dir = sys.path[0]
        # print(main_dir)
        token = os.path.join(main_dir, 'token.txt')
        with open(token, 'r') as tk:
            api_token = tk.read()
        vk_ses = vk_api.VkApi(token=api_token)
        longpoll = VkBotLongPoll(vk_ses, '187245504', wait=25)

        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW and event.object.message['from_id'] > 0:
                time_of_operation_start = time.time()
                new_event = Event(MESSAGE_EVENT, event.object.message['peer_id'], event.object.message['from_id'], text=event.object.message['text'].lower())
                processing(new_event, games)
                time_of_operation_end = time.time()
                # print('Operation time: ' + str(time_of_operation_end - time_of_operation_start))
    if regime == 'TEST':
        users_number = 5
        peer_id = 101
        # print(users_number)
        """TEST"""

        event = Event(MESSAGE_EVENT, peer_id, 1, text='registration')
        processing(event, games)

        for i in range(users_number):
            from_id = i
            event = Event(MESSAGE_EVENT, peer_id, from_id, text='ja')
            processing(event, games)

        event = Event(MESSAGE_EVENT, peer_id, 1, text='start')
        processing(event, games)
        game = get_game(peer_id, games)
        while game.status is not None:

            event = Event(MESSAGE_EVENT, peer_id, game.get_president().from_id, text=str(random.randint(0, len(game.gamers_list))))
            # print(f'msg from {event.from_id}: {event.text}')
            processing(event, games)

            for gamer in game.gamers_list:
                a = random.randint(0, 10)
                if a == 0:
                    r = 'n'
                else:
                    r = 'j'
                event = Event(MESSAGE_EVENT, peer_id, gamer.from_id, text=r)
                # print(f'msg from {event.from_id}: {event.text}')
                processing(event, games)
            if game.status is not None:
                president = game.get_president()
                n = random.randint(1, 3)
                event = Event(MESSAGE_EVENT, peer_id, president.from_id, text=str(n))
                # print(f'msg from {event.from_id}: {event.text}')
                processing(event, games)

                chancellor = game.get_chancellor()
                n = random.randint(1, 2)
                if game.veto and not game.veto_rejected:
                    event = Event(MESSAGE_EVENT, peer_id, chancellor.from_id, text='вето')
                else:
                    event = Event(MESSAGE_EVENT, peer_id, chancellor.from_id, text=str(n))
                # print(f'msg from {event.from_id}: {event.text}')
                processing(event, games)

                if game.president_veto_request:
                    event = Event(MESSAGE_EVENT, peer_id, president.from_id, text='n')
                    processing(event, games)
                if game.loyalty_request or game.exec_request or game.special_elect_request:
                    event = Event(MESSAGE_EVENT, peer_id, president.from_id, text=str(1))
                    processing(event, games)
#
while True:
    main('PROD')

# main('TEST')
