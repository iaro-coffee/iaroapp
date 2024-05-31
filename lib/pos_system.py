from abc import ABC, abstractmethod

from lib.model.customer_card import CustomerCard


class POSSystem(ABC):

    @abstractmethod
    def create_customer_card(self, card_id, balance=0) -> bool:
        # create card at POS end system
        # potentially also create QR-Code
        # set card balance if provided
        # returns success/failure
        pass

    @abstractmethod
    def get_customer_card(self, card_id) -> CustomerCard:
        # get card from POS
        pass

    @abstractmethod
    def get_customer_card_balance(self, card_id) -> int:
        pass

    @abstractmethod
    def set_customer_card_balance(self, card_id, balance) -> bool:
        # returns success/failure
        pass
