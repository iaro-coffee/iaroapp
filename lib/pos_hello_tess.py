import json
import logging
import os

import requests
from dotenv import find_dotenv, load_dotenv

from lib.model.customer_card import CustomerCard
from lib.pos_system import POSSystem

logger = logging.getLogger(__name__)

load_dotenv(find_dotenv())


class POSHelloTess(POSSystem):
    api_key = os.environ["HELLO_TESS_KEY"]
    base_url = "https://iaro.bo3.hellotess.com/v1"
    session = requests.session()
    session.trust_env = False  # TODO(Rapha): check what this does
    auth_headers = {
        "hellotess-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def create_customer_card(self, card_id, balance=0) -> bool:
        # 1. create card
        payload = {"id": card_id}
        response = self.session.request(
            "POST",
            self.base_url + "/cards",
            headers=self.auth_headers,
            json=payload,
        )

        if response.status_code != 200:
            logger.error(
                f"Creating Card failed with statuscode: {response.status_code}"
            )
            return False

        # 2. top up card balance
        if balance == 0:
            return True

        return self.set_customer_card_balance(card_id, balance)

    def get_customer_card(self, card_id) -> CustomerCard:
        response = self.session.request(
            "GET", self.base_url + "/cards/id/" + card_id, headers=self.auth_headers
        )

        if response.status_code != 200:
            logger.error(
                f"Getting customer card failed with code: {response.status_code}"
            )
            raise ValueError("Customer Card could not be retrieved from Hello Tess")

        response = json.loads(response.text)

        # TODO(Rapha): as soon as API returns balance, update balance here
        return CustomerCard(
            card_id=card_id,
            user_group_id=response["userGroupId"],
            card_type=response["type"],
            balance=0,
            active=response["active"],
        )

    def get_customer_card_balance(self, card_id) -> int:
        customer_card = self.get_customer_card(card_id)
        return customer_card.balance

    def set_customer_card_balance(self, card_id, balance) -> bool:
        payload = {"cardId": card_id, "balance": balance}
        response = self.session.request(
            "POST",
            self.base_url + "/cards/balance",
            headers=self.auth_headers,
            json=payload,
        )

        if response.status_code != 200:
            logger.error(
                f"Setting card balance failed with statuscode: {response.status_code}"
            )
            return False
        return True
