# Write your code here
import sqlite3
import os


pro_struct = dict()
state = ''
# 'welcome', 'logged_in', 'exit'

user_db_con: sqlite3.Connection = None
# user_data = {
#     'id': [],
#     'user_card_nr': [],
#     'card_nr': [],
#     'pin': [],
#     'balance': []
# }  # {id:[index], card nr:[], pin:[], balance:[]}

logged_in_user_id = None


def _create_program_struct() -> dict:
    p = dict()
    p['welcome'] = {
        '1': ['Create an accout', _create_account_],
        '2': ['Log into account', _log_into_account_],
        '0': ['Exit', _exit_pro]
    }
    p['create_account'] = {
    }
    p['logged_in'] = {
        '1': ['Balance', _check_balance_],
        '2': ['Add income', _add_income],
        '3': ['Do transfer', _do_transfer],
        '4': ['Close account', _close_account],
        '5': ['Log out', _log_out],
        '0': ['Exit', _exit_pro]
    }
    return p


def _close_account():
    global user_db_con
    global logged_in_user_id
    cur = user_db_con.cursor()
    cur.execute("""
            DELETE FROM card WHERE id = ?
        """, (logged_in_user_id,))
    user_db_con.commit()
    _log_out()
    print('The account has been closed!')
    print()

def _do_transfer():
    print('Transfer')
    print('Enter card number:')
    card_nr_str = input()

    # check nr
    check_sum = _get_checksum_luhn(card_nr_str[:-1])
    # print('DBEUG: card_nr_str', card_nr_str)
    # print('DEBUG: card nr piece', card_nr_str[:-1])
    # print('DEBUG: check_sum', check_sum)
    if card_nr_str[-1] != check_sum:
        print('Probably you made a mistake in the card number. '
              'Please try again!')
        return

    # find card
    global user_db_con
    cur = user_db_con.cursor()
    res = cur.execute("""
        SELECT id FROM card WHERE number == ?
        """, (card_nr_str,))

    card_id = res.fetchall()

    if not card_id:  # empty
        print('Such a card does not exist.')
        return

    global logged_in_user_id
    to_card_id = card_id[0][0]
    if to_card_id == logged_in_user_id:
        print("You can't transfer money to the same account!")
        return

    # transfer money if enough
    print('Enter how much money you want to transfer:')
    to_trans_amount = int(input())
    cur = user_db_con.cursor()
    res = cur.execute("""
        SELECT balance FROM card WHERE id == ?;
        """, (logged_in_user_id,))
    balance = res.fetchall()[0][0]
    if balance < to_trans_amount:
        print('Not enough money!')
    else:
        # do trans
        # cur.execute("""
        #     BEGIN TRANSACTION;
        #         UPDATE card
        #         SET balance = balance - ?
        #         WHERE id = ?;
        #
        #         UPDATE card
        #         set balance = balance + ?
        #         WHERE number = ?;
        #     COMMIT;
        # """, (to_trans_amount,
        #       logged_in_user_id,
        #       to_trans_amount,
        #       card_nr_str))
        # user_db_con.commit()

        # substr
        cur.execute("""
        UPDATE card
        SET balance = balance - ?
        WHERE id = ?;
        """,(to_trans_amount, logged_in_user_id))
        user_db_con.commit()

        # add
        cur.execute("""
        UPDATE card
        SET balance = balance + ?
        WHERE number = ?;
        """,(to_trans_amount, card_nr_str))
        user_db_con.commit()
        print('Success!')
    print()




def _add_income():
    print('Enter income')
    income = int(input())
    global user_db_con
    global logged_in_user_id

    cur = user_db_con.cursor()
    cur.execute("""
        UPDATE card
        SET balance = balance + ?
        WHERE id == ?
    """, (income, logged_in_user_id))
    user_db_con.commit()
    print('Income was added!')
    print()


def _f_all_p(res: list[tuple]) ->list:
    res_l = []
    for r in res:
        res_l.append(r[0])
    return res_l

def _get_all_card_nrs() -> list[str]:
    global user_db_con
    cur = user_db_con.cursor()

    res = cur.execute("""
    SELECT number FROM card;
    """)
    res_l = _f_all_p(res.fetchall())
    return res_l

def _gen_user_id_nr_from_card_nrs(card_nr_l: list[str],
                                  mii,
                                  checksum_length = 1) -> list[str]:
    user_ids = []
    for card_nr in card_nr_l:
        uid = card_nr[len(mii):-checksum_length]
        user_ids.append(uid)
    return user_ids


def _create_card_nr(mii: str = '400', card_nr_length: int = 16):
    all_card_nrs = _get_all_card_nrs()
    # print(all_card_nrs)
    user_ids = _gen_user_id_nr_from_card_nrs(all_card_nrs, mii)
    # print(user_ids)

    # user id nr
    if len(user_ids) == 0:
        user_id_nr = '0' * (card_nr_length-len(mii)-1)
    else:
        user_id_nr = str(max(list(map(int, user_ids)))+10)
        # print(len(user_id_nr))
        user_id_nr = '0' * (card_nr_length - len(mii) - 1 - len(user_id_nr)) + user_id_nr
        # print(len(user_id_nr))

    # checksum
    checksum = _get_checksum_luhn(mii+user_id_nr)

    return mii + user_id_nr + checksum


def _get_checksum_luhn(nr_str: str) -> str:
    nr_list = []
    for i, char in enumerate(nr_str):
        nr = int(char)
        if (i+1) % 2 == 0:
            nr_list.append(nr)
        else:
            double = 2 * nr
            if double > 9:
                nr_list.append(double - 9)
            else:
                nr_list.append(double)

    nr_sum = sum(nr_list)
    if nr_sum % 10 == 0:
        checksum = 0
    else:
        checksum = 10 - nr_sum % 10
    # print(checksum)
    return str(checksum)


### menu functions
# def _create_account():
#     base = 4000000000000000
#     #base = '4'
#     global user_data
#     uid = len(user_data['id'])-1
#     card_nr, user_card_nr = _create_card_nr()
#     pin = '1234'
#     balance = 0
#
#     user_data['id'].append(uid)
#     user_data['user_card_nr'].append(user_card_nr)
#     user_data['card_nr'].append(card_nr)
#     user_data['pin'].append(pin)
#     user_data['balance'].append(balance)
#
#     print('Your card bas been created')
#     print('Your card number:')
#     print(card_nr)
#     #print(len(card_nr))
#     print('your card PIN:')
#     print(pin)
#     print()

def _create_account_():
    global user_db_con
    card_nr = _create_card_nr()
    pin = '1234'

    cur = user_db_con.cursor()
    cur.execute("""
    INSERT INTO card (number, pin) VALUES
    (?, ?)
    """, (card_nr, pin))
    user_db_con.commit()

    print('Your card bas been created')
    print('Your card number:')
    print(card_nr)
    # print(len(card_nr))
    print('your card PIN:')
    print(pin)
    print()


def _log_into_account_():
    u_id = None
    print('Enter your card number:')
    c_nr = input()
    print('Enter your PIN:')
    pin = input()

    global user_db_con
    cur = user_db_con.cursor()
    res = cur.execute("""
    SELECT id FROM card WHERE number == ?
    """, (c_nr,))
    u_id_sq = res.fetchall()

    if not u_id_sq:  # empty sequence
        print('Wrong Card Number or PIN!')
        print()
    else:
        u_id = u_id_sq[0][0]
        # check pin
        res = cur.execute("""
        SELECT pin FROM card WHERE id = ?
        """, (u_id,))
        u_pin = res.fetchall()[0][0]
        if u_pin == pin:
            print('You have successfully logged in!')
            print()
            global state
            state = 'logged_in'
            global logged_in_user_id
            logged_in_user_id = u_id
        else:
            print('Wrong Card Number or PIN!')
            print()


# def _log_into_account():
#     u_id = None
#     print('Enter your card number:')
#     c_nr = input()
#     print('Enter your PIN:')
#     pin = input()
#
#     try:
#         u_id = user_data['card_nr'].index(c_nr)
#     except ValueError:
#         print('Wrong Card Number or PIN!')
#         print()
#     else:
#         if user_data['pin'][u_id] == pin:
#             print('You have successfully logged in!')
#             print()
#             global state
#             state = 'logged_in'
#             global logged_in_user_id
#             logged_in_user_id = u_id
#         else:
#             print('Wrong Card Number or PIN!')
#             print()


def _exit_pro():
    global state
    state = 'exit'
    print('Bye!')

# def _check_balance():
#     global logged_in_user_id
#     global user_data
#     print('Balance: ' + str(user_data['balance'][logged_in_user_id]))
#     print()

def _check_balance_():
    global logged_in_user_id
    global user_db_con
    cur = user_db_con.cursor()
    res = cur.execute("""
    SELECT balance FROM card WHERE id == ?;
    """, (logged_in_user_id,))
    balance = res.fetchall()[0][0]

    print('Balance: ' + str(balance))
    print()


def _log_out():
    global state
    state = 'welcome'
    global logged_in_user_id
    logged_in_user_id = None


def _print_state_menu():
    global pro_struct
    global state
    d = pro_struct[state]
    for k, l in d.items():
        print(str(k) + '. ' + l[0])


def _process_ui(ui: str):
    global pro_struct
    global state
    d = pro_struct[state]
    if ui in d:
        d[ui][1]()


def _init_db(con: sqlite3.Connection, cur: sqlite3.Cursor):
    cur.execute("""
    CREATE TABLE card(
        id INTEGER PRIMARY KEY,
        number TEXT UNIQUE,
        pin TEXT DEFAULT '1234',
        balance INTEGER DEFAULT 0
    );
    """)
    con.commit()



def _get_db(db_url: str) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    # check if db file exists
    if os.path.isfile(db_url):
        # if file exists, we assume it has been initialsed as well
        con = sqlite3.connect(db_url)
        cur = con.cursor()
    else:
        con = sqlite3.connect(db_url)
        cur = con.cursor()
        _init_db(con, cur)
    return con, cur


### main pro loop
def main():
    global pro_struct
    pro_struct = _create_program_struct()

    global state
    state = 'welcome'

    global user_db_con
    user_db_con, _ = _get_db('./card.s3db')

    while state != 'exit':

        _print_state_menu()
        ui = input()
        print()
        _process_ui(ui)

    user_db_con.close()


if __name__ == '__main__':
    main()
