from gamer import Gamer


class Liberal(Gamer):
    def print_role(self):
        print(f'{self.from_id} is Liberal in {self.peer_id}')