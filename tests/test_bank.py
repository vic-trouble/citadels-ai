import pytest

from citadels.game import Bank, GameError


def test_cash_into_account():
    # arrange
    bank = Bank()
    account = bank.account('player')

    # act
    gold = account.cash_in(10)

    # assert
    assert gold == 10
    assert account.balance == 10


def test_withdraw_from_account():
    # arrange
    bank = Bank()
    account = bank.account('player')
    account.cash_in(10)

    # act
    gold = account.withdraw(1)

    # assert
    assert gold == 1
    assert account.balance == 9


def test_no_overdraft_on_account():
    # arrange
    bank = Bank()
    account = bank.account('player')
    account.cash_in(10)

    # assert
    with pytest.raises(GameError):
        account.withdraw(11)
