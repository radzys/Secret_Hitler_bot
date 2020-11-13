import re
import random
import time
import os
import sys
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
import vk_api
from liberal import Liberal
from fascist import Fascist
from hitler import Hitler

START_TIME = time.time()
main_dir = sys.path[0]
token = os.path.join(main_dir, 'token.txt')
with open(token, 'r') as tk:
    api_token = tk.read()
vk_ses = vk_api.VkApi(token=api_token)
longpoll = VkBotLongPoll(vk_ses, '187245504', wait=25)


class GameError(BaseException):
    pass


def send_msg(recipient: int, text=None):
    """
    Sends message to any (it is an important difference from Message.reply method)
     conversation using VK API
    :param attachment: Message attach
    :param recipient: id of recipient
    :param text: Text of message
    """
    vk_ses.method('messages.send', {'peer_id': recipient,
                                    'message': text,
                                    'random_id': random.randint(1, 100000)})


def info_message(to, message):
    # print(f'Message to {to}: {message}')
    # with open('log.txt', 'a') as out:
    #     out.write(f'{round(time.time() - START_TIME, 2)} : TO {to} : {message}\n')
    send_msg(to, message)


class Game:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.status = None
        self.election_status = False
        self.chancellor_choose_status = False
        self.counting_status = False
        self.users_list = []
        self.gamers_list = []
        self.number_of_gamers = 0
        self.REGISTRATION_PATTERN = 'reg'
        self.START_PATTERN = 'start'
        self.JA_PATTERN = 'ja'
        self.NEIN_PATTERN = 'nein'
        self.VETO_PATTERN = 'вето'
        self.used_deck = []
        self.deck = []
        self.president_num = -1
        self.chancellor_candidates = {}
        self.voted = []
        self.chancellor_candidate = None
        self.failed_votes = 0
        self.report = {}
        self.j_count = 0
        self.n_count = 0
        self.president_cards = False
        self.chancellor_cards = False
        self.loyalty_request = False
        self.veto_active = False
        self.loyalty_check = {}
        self.extra_president = {}
        self.killing_list = {}
        self.exec_request = False
        self.special_elect_request = False
        self.president_veto_request = False
        self.cards = []
        self.laws = ''
        self.veto = False
        self.veto_rejected = False
        self.last_president = None
        self.last_chancellor = None

    def clean(self):
        info_message(self.peer_id, 'Игра закончена')
        self.status = None
        self.election_status = False
        self.chancellor_choose_status = False
        self.counting_status = False
        self.users_list = []
        self.gamers_list = []
        self.number_of_gamers = 0
        self.REGISTRATION_PATTERN = 'reg'
        self.START_PATTERN = 'start'
        self.JA_PATTERN = 'ja'
        self.NEIN_PATTERN = 'nein'
        self.VETO_PATTERN = 'вето'
        self.used_deck = []
        self.deck = []
        self.president_num = -1
        self.chancellor_candidates = {}
        self.voted = []
        self.chancellor_candidate = None
        self.failed_votes = 0
        self.report = {}
        self.j_count = 0
        self.n_count = 0
        self.president_cards = False
        self.chancellor_cards = False
        self.loyalty_request = False
        self.veto_active = False
        self.loyalty_check = {}
        self.extra_president = {}
        self.killing_list = {}
        self.exec_request = False
        self.special_elect_request = False
        self.president_veto_request = False
        self.cards = []
        self.laws = ''
        self.veto = False
        self.veto_rejected = False
        self.last_president = None
        self.last_chancellor = None

    def receive_message(self, event):
        with open('log.txt', 'a') as out:
            out.write(f'{round(time.time() - START_TIME, 2)} : FROM {event.from_id} : {event.text}\n')
        if re.search(self.REGISTRATION_PATTERN, event.text) and self.status is None:
            self.registration()
        if self.status == 'REG' and re.search(self.JA_PATTERN, event.text):
            self.new_gamer(event.from_id)
        if re.search(self.START_PATTERN, event.text) and self.status == "REG":
            self.start()
        if self.status == 'RUN' and self.is_gamer_check(event):
            if self.check_game_end(hitler=False):
                if self.chancellor_choose_status and re.match('^[0-9]+$', event.text) and event.from_id == self.get_president().from_id:
                    self.chancellor_choose(event)
                    return
                if (event.text == 'j' or event.text == 'n') and self.counting_status == True and self.user_in_gamers(event.from_id):
                    self.counting_of_votes(event)
                    return
                if not self.counting_status and self.president_cards and event.from_id == self.get_president().from_id or self.chancellor_cards and event.from_id == self.get_chancellor().from_id:
                    self.cards_from(event)
                    return
                if event.from_id == self.get_president().from_id:
                    if self.loyalty_request and re.match('^[0-9]+$', event.text):
                        self.investigate_loyalty_response(event)
                        return
                    if self.special_elect_request and re.match('^[0-9]+$', event.text):
                        self.special_election_response(event)
                        return
                    if self.exec_request and re.match('^[0-9]+$', event.text):
                        self.execution_response(event)
                    if self.veto and (event.text == 'j' or event.text == 'n') and self.veto_active:
                        self.veto_response(event)
        if self.status is not None and re.search('stop', event.text):
            self.clean()

    def is_gamer_check(self, event):
        for gamer in self.gamers_list:
            if gamer.from_id == event.from_id:
                return True
        return False

    def check_game_end(self, hitler=True):
        if len(self.gamers_list) > 0:
            laws = self.laws.split()
            i = 0
            for gamer in self.gamers_list:
                if type(gamer).__name__ == 'Hitler':
                    i += 1
            if i == 0:
                info_message(self.peer_id, 'Гитлер был убит')
                self.status = None
                self.clean()
                return False
            if len(laws) >= 5:
                f_count = 0
                l_count = 0
                for law in laws:
                    if law == 'F':
                        f_count += 1
                    if law == 'L':
                        l_count += 1
                if l_count == 5:
                    info_message(self.peer_id, 'Принято 5 либеральных законов')
                    self.status = None
                    self.clean()
                    return False
                if f_count >= 3 and hitler:
                    if type(self.get_chancellor()).__name__ == "Hitler":
                        info_message(self.peer_id, 'Гитлер был выбран канцлером')
                        self.status = None
                        self.clean()
                        return False
                if f_count == 6:
                    info_message(self.peer_id, 'Принято 6 фашистских законов')
                    self.status = None
                    self.clean()
                    return False
        return True

    def president_power(self):
        laws = self.laws.split()
        c = 0
        for law in laws:
            if law == 'F':
                c += 1

        if self.number_of_gamers in [5, 6]:
            if c <= 2:
                pass
            if c == 3:
                self.policy_peek()
            if c == 4:
                self.execution_request()
            if c == 5:
                self.execution_request()
                self.veto = True

        if self.number_of_gamers in [7, 8]:
            if c <= 1:
                pass
            if c == 2:
                self.investigate_loyalty_request()
            if c == 3:
                self.special_election_request()
            if c == 4:
                self.execution_request()
            if c == 5:
                self.execution_request()
                self.veto = True

        if self.number_of_gamers in [9, 10]:
            if c <= 1:
                self.investigate_loyalty_request()
            if c == 2:
                self.investigate_loyalty_request()
            if c == 3:
                self.special_election_request()
            if c == 4:
                self.execution_request()
            if c == 5:
                self.execution_request()
                self.veto = True

    def user_in_gamers(self, user):
        for gamer in self.gamers_list:
            if gamer.from_id == user:
                return True
        return False

    def registration(self):
        info_message(self.peer_id, 'Начата регистрация')
        if self.status is None:
            self.status = 'REG'
        else:
            raise GameError

    def start(self):
        if self.status == 'REG' and len(self.users_list) < 1:
            self.send_message('Слишком мало игроков')
        elif self.status == 'REG':
            self.status = 'RUN'
            self.procedures()

    def finish(self):
        if self.status == 'RUN':
            self.status = None
        else:
            raise GameError

    def send_message(self, message):
        print(f'Game message to {self.peer_id}: {message}')
        info_message(self.peer_id, message)

    def new_gamer(self, from_id):
        if self.status == "REG" and from_id not in self.users_list:
            if len(self.users_list) < 10:
                self.users_list.append(from_id)
                info_message(self.peer_id, f'Вы добавлены, осталось {10 - len(self.users_list)} мест')
            else:
                self.send_message('Слишком много игроков')
                self.clean()

    def get_number_of_fascist(self, users_list):
        if self.status == 'RUN':
            users_number = len(users_list)
            if users_number in [5, 6]:
                return 1
            elif users_number in [7, 8]:
                return 2
            elif users_number in [9, 10]:
                return 3
        else:
            raise GameError

    def create_gamers(self):
        users_id_list_copy = self.users_list
        fascist_number = self.get_number_of_fascist(users_id_list_copy)
        liberal_number = len(users_id_list_copy) - fascist_number - 1
        random.shuffle(users_id_list_copy)
        gamers_list = []

        fascist_counter = 0
        liberal_counter = 0

        while len(users_id_list_copy) > 0:
            user = users_id_list_copy.pop()
            if liberal_counter < liberal_number:
                gamer = Liberal(user, self.peer_id)
                gamers_list.append(gamer)
                liberal_counter += 1
                continue
            if fascist_counter < fascist_number:
                gamer = Fascist(user, self.peer_id)
                gamers_list.append(gamer)
                fascist_counter += 1
            else:
                gamer = Hitler(user, self.peer_id)
                gamers_list.append(gamer)
        random.shuffle(gamers_list)
        self.gamers_list = gamers_list
        self.number_of_gamers = len(self.gamers_list)

    def get_comrades(self, gamer_1):
        gamers_list = self.gamers_list
        role_gamer_1 = type(gamer_1).__name__
        if (len(gamers_list) < 7 and (role_gamer_1 == 'Fascist' or role_gamer_1 == 'Hitler')) or (
                len(gamers_list) >= 7 and role_gamer_1 == 'Fascist'):
            comrade_list = f'Ваша роль — {role_gamer_1}\nВаши союзники:\n'
            for gamer_2 in gamers_list:
                if gamer_1 != gamer_2:
                    if type(gamer_2).__name__ == 'Fascist':
                        comrade_list += f'{gamer_2.name} – Fascist\n'
                    elif type(gamer_2).__name__ == 'Hitler':
                        comrade_list += f'{gamer_2.name} – Hitler\n'
            comrade_list = comrade_list[:-1]
            return comrade_list
        else:
            return f'Ваша роль {role_gamer_1}'

    def info_comrades(self):
        gamers_list = self.gamers_list
        for gamer in gamers_list:
            comrades = self.get_comrades(gamer)
            if comrades is not None:
                info_message(gamer.from_id, comrades)

    def get_chancellor(self):
        for gamer in self.gamers_list:
            if gamer.is_chancellor:
                return gamer
        return self.gamers_list[0]

    def get_president(self):
        for gamer in self.gamers_list:
            if gamer.is_president:
                return gamer
        return self.gamers_list[0]

    def get_was_chancellor(self):
        for gamer in self.gamers_list:
            if gamer.was_chancellor:
                return gamer

    def get_was_president(self):
        for gamer in self.gamers_list:
            if gamer.was_president:
                return gamer

    def get_gamer_by_from_id(self, from_id):
        for gamer in self.gamers_list:
            if gamer.from_id == from_id:
                return gamer
        return self.gamers_list[0]

    def pre_chancellor_choose(self):
        message = "Вы должны выбрать своего канцлера\nОтправьте в ответ его номер из списка:\n"
        i = 0
        self.chancellor_candidates = {}
        for gamer in self.gamers_list:
            if not gamer.is_president and gamer != self.last_chancellor and gamer != self.last_president:
                i += 1
                message += f'{i}: {gamer.name}\n'
                self.chancellor_candidates[i] = gamer
        message = message[:-1]
        president = self.get_president()
        info_message(president.from_id, message)
        self.chancellor_choose_status = True

    def chancellor_choose(self, event):
        control = False
        try:
            chancellor_num = int(event.text)
            control = True
        except ValueError:
            info_message(event.from_id, "Что-то не так, попробуйте еще раз")
        if control:
            try:
                self.election('Chancellor', self.chancellor_candidates[chancellor_num])
                self.chancellor_candidate = self.chancellor_candidates[chancellor_num]
                self.chancellor_choose_status = False
                self.counting_status = True
            except KeyError:
                info_message(event.from_id, "Что-то не так, попробуйте еще раз")

    def new_chancellor(self, gamer):
        old_chancellor = self.get_chancellor()
        try:
            old_chancellor.is_chancellor = False
            old_chancellor.was_chancellor = True
        except AttributeError:
            pass
        gamer.is_chancellor = True

    def new_president(self, special=None, failed_voting=False):
        if self.check_game_end(hitler=False):
            if not (self.loyalty_request or self.exec_request or self.special_elect_request):
                if self.president_num != -1:
                    old_president = self.get_president()
                    if not failed_voting:
                        old_president.is_president = False
                        # old_president.was_president = True
                    else:
                        pass
                if special:
                    special.is_president = True
                else:
                    if self.president_num < len(self.gamers_list) - 1:
                        self.president_num += 1
                    else:
                        self.president_num = 0
                    self.gamers_list[self.president_num].is_president = True
                self.pre_chancellor_choose()
        else:
            return

    def election(self, obj, person):
        self.election_status = True
        if obj == 'Chancellor':
            president = self.get_president()
            chancellor = person
            for gamer in self.gamers_list:
                message = f'{president.name} предложил {chancellor.name} на роль канцлера\n'
                message += 'Вы согласны? Напишите j если да или n если нет'
                info_message(gamer.from_id, message)

    def counting_of_votes(self, event):
        if event.from_id not in self.voted:
            if event.text == 'j':
                self.j_count += 1
                self.report[self.get_gamer_by_from_id(event.from_id).name] = 'за'
                self.voted.append(event.from_id)
            if event.text == 'n':
                self.n_count += 1
                self.report[self.get_gamer_by_from_id(event.from_id).name] = 'против'
                self.voted.append(event.from_id)
        if len(self.voted) == len(self.gamers_list):
            message = "Результаты голосования:\n"
            for gamer in self.report:
                message += f'{gamer} проголосовал {self.report[gamer]}\n'
            message += '\n'
            message += 'Общее решение: '
            if self.n_count >= self.j_count:
                message += 'НЕТ'
                info_message(self.peer_id, message)
                self.failed_votes += 1
                if self.failed_votes == 3:
                    if len(self.deck) > 0:
                        card = self.deck.pop()
                        self.laws += f'{card} '
                        message = f'В связи с 3 проваленными голосованиями принят {card} закон. Принятые ' \
                                  f'законы:\n{self.laws} '
                        self.used_deck.append(card)
                        info_message(self.peer_id, message)
                        self.check_game_end()
                        self.failed_votes = 0
                self.new_president(failed_voting=True)
                self.chancellor_candidate = None
                self.voted = []
                self.report = {}
            else:
                message += 'ДА'
                info_message(self.peer_id, message)

                self.new_chancellor(self.chancellor_candidate)
                self.last_president = self.get_president()
                self.last_chancellor = self.get_chancellor()
                if self.check_game_end():
                    self.cards_to_president()
            self.voted = []
            self.report = {}
            self.j_count = 0
            self.n_count = 0
            self.counting_status = False
            self.election_status = False

    def init_deck(self):
        for _ in range(6):
            self.deck.append('L')
        for _ in range(11):
            self.deck.append('F')
        random.shuffle(self.deck)

    def cards_to_president(self):
        cards = {}
        self.president_cards = True
        if len(self.deck) > 2:
            for i in range(3):
                card = self.deck.pop()
                cards[i + 1] = card
                self.cards.append(card)
        else:
            for _ in range(len(self.deck)):
                self.used_deck.append(self.deck.pop())
            self.deck = self.used_deck
            random.shuffle(self.deck)
            self.used_deck = []
            for i in range(3):
                card = self.deck.pop()
                cards[i + 1] = card
                self.cards.append(card)

        message = 'Выберите карту для сброса и отправьте в ответ её номер:\n'
        for card in cards:
            message += f'{card}: {cards[card]}\n'
        message = message[:-1]
        info_message(self.get_president().from_id, message)

    def cards_to_chancellor(self):
        cards = {}
        for i in range(2):
            cards[i + 1] = self.cards[i]
        if not self.veto:
            message = 'Выберите карту для сброса и отправьте в ответ её номер:\n'
            for card in cards:
                message += f'{card}: {cards[card]}\n'
            message = message[:-1]
            info_message(self.get_chancellor().from_id, message)
        else:
            message = 'Выберите карту для сброса и отправьте в ответ её номер или напишите "вето", чтобы запросить ' \
                      'право вето:\n'

            for card in cards:
                message += f'{card}: {cards[card]}\n'
            message = message[:-1]
            info_message(self.get_chancellor().from_id, message)

    def cards_from(self, event):
        self.check_game_end()
        if self.veto and event.text == self.VETO_PATTERN and event.from_id == self.get_chancellor().from_id and not self.veto_rejected:
            self.president_veto_request = True
            info_message(self.get_president().from_id, 'Канцлер запросил вето. Вы согласны? Напишите в ответ j или n')
            info_message(self.peer_id, 'Канцлер запросил вето')
            self.veto_active = True
        else:
            try:
                num = int(event.text)
            except ValueError:
                info_message(event.from_id, 'Что-то не так, попробуйте еще раз')
                return
            if num <= 0 or num > len(self.cards):
                info_message(event.from_id, 'Такого номера нет')
            else:
                self.used_deck.append(self.cards.pop(num - 1))
                if self.president_cards:
                    self.president_cards = False
                    self.chancellor_cards = True
                    self.cards_to_chancellor()
                elif self.chancellor_cards:

                    self.chancellor_cards = False
                    self.laws += f'{self.cards[0]} '
                    laws_list = self.laws.split()
                    lib = ''
                    fas = ''
                    for law in laws_list:
                        if law == 'L':
                            lib += f'{law} '
                        if law == 'F':
                            fas += f'{law} '

                    message = f'Принят {self.cards[0]} закон. Принятые законы:\n{lib}\n{fas}'
                    if self.cards[0] == 'F':
                        fascist_law = True
                    else:
                        fascist_law = False
                    info_message(self.peer_id, message)
                    self.veto_rejected = False
                    self.used_deck.append(self.cards.pop())
                    if fascist_law:
                        self.president_power()
                    if self.check_game_end(hitler=False):
                        self.new_president()

    def policy_peek(self):
        if len(self.deck) < 3:
            for _ in range(len(self.deck)):
                self.used_deck.append(self.deck.pop())
            self.deck = self.used_deck
            random.shuffle(self.deck)
            self.used_deck = []

        laws = ''
        for i in range(1, 4):
            laws += f'{self.deck[- i]} '
        laws = laws[:-1]
        info_message(self.get_president().from_id, f'Следующие три закона в колоде: {laws}')

    def investigate_loyalty_request(self):
        message = 'Вы можете узнать за какую команду играет любой из игроков\n'
        message += 'Выберите из списка ниже его номер и отправьте в ответ:\n'
        i = 0
        for gamer in self.gamers_list:
            if not gamer.is_president and not gamer.loyalty_checked:
                i += 1
                message += f'{i}: {gamer.name}\n'
                self.loyalty_check[i] = gamer
        message = message[:-1]
        info_message(self.get_president().from_id, message)
        self.loyalty_request = True

    def investigate_loyalty_response(self, event):
        number = int(event.text)
        if number > len(self.loyalty_check) or number <= 0:
            info_message(event.from_id, 'Такого номера нет')
        else:
            gamer = self.loyalty_check[number]
            gamer.loyalty_checked = True
            message = f'Вы выбрали игрока {gamer.name}. Его команда - '
            if type(gamer).__name__ == "Fascist" or type(gamer).__name__ == "Hitler":
                message += 'Fascist'
            else:
                message += 'Liberal'
            info_message(event.from_id, message)
            self.loyalty_request = False
            self.new_president()

    def special_election_request(self):
        message = 'Вы можете выбрать следующего президента\n'
        message += 'Выберите из списка ниже его номер и отправьте в ответ:\n'
        i = 0
        for gamer in self.gamers_list:
            if not gamer.is_president:
                i += 1
                message += f'{i}: {gamer.name}\n'
                self.extra_president[i] = gamer
        message = message[:-1]
        info_message(self.get_president().from_id, message)
        self.special_elect_request = True

    def special_election_response(self, event):
        number = int(event.text)
        if number > len(self.loyalty_check) or number <= 0:
            info_message(event.from_id, 'Такого номера нет')
        else:
            gamer = self.extra_president[number]
            message = f'Вы выбрали игрока {gamer.name}'
            info_message(event.from_id, message)
            self.special_elect_request = False
            self.extra_president = {}
            self.new_president(gamer)

    def execution_request(self):
        message = 'Вы можете убить любого игрока\n'
        message += 'Выберите из списка ниже его номер и отправьте в ответ:\n'
        i = 0
        for gamer in self.gamers_list:
            if not gamer.is_president:
                i += 1
                message += f'{i}: {gamer.name}\n'
                self.killing_list[i] = gamer
        message = message[:-1]
        info_message(self.get_president().from_id, message)
        self.exec_request = True

    def execution_response(self, event):
        number = int(event.text)
        if number > len(self.killing_list) or number <= 0:
            info_message(event.from_id, 'Такого номера нет')
        else:
            gamer = self.killing_list[number]
            message = f'Вы выбрали игрока {gamer.name}'
            info_message(event.from_id, message)
            self.exec_request = False
            self.killing_list = {}
            info_message(self.peer_id, f'Президент {self.get_president().name} убил игрока {gamer.name}')
            i = 0
            for user in self.gamers_list:
                if user == gamer:
                    self.gamers_list.pop(i)
                i += 1
            if self.check_game_end(hitler=False):
                self.new_president()

    def veto_response(self, event):
        self.veto_active = False
        if event.text == 'j':
            info_message(self.peer_id, 'Президент подтвердил вето. Назначается следующий президент')
            self.new_president()
        else:
            info_message(self.peer_id, 'Президент отклонил вето. Канцлер выбирает закон')
            self.chancellor_cards = True
            self.veto_rejected = True
            self.cards_to_chancellor()

    def procedures(self):
        self.create_gamers()
        self.info_comrades()
        self.init_deck()
        self.new_president()




