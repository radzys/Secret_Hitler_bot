from gamer import Gamer


class Hitler(Gamer):
    def print_role(self):
        print(f'{self.from_id} is Hitler in {self.peer_id}')