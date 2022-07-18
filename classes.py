from audioop import add


DIAM, CLUB, HEART, SPADE = 0, 1, 2, 3
SUIT_NAMES = {DIAM: "diam", CLUB: "club", HEART: "heart", SPADE: "spade"}

ROYAL_FLUSH = 10
STRAIGHT_FLUSH = 9
FOUR_OF_A_KIND = 8
FULL_HOUSE = 7
FLUSH = 6
STRAIGHT = 5
THREE = 4
TWO_PAIR = 3
PAIR = 2
HIGH = 1
WIN_NAMES = {ROYAL_FLUSH: 'royal flush', STRAIGHT_FLUSH: 'straight flush', FOUR_OF_A_KIND: 'four of a kind',
             FULL_HOUSE: 'full house', FLUSH: 'flush', STRAIGHT: 'straight', THREE: 'three of a kind',
             TWO_PAIR: 'two pair', PAIR: 'pair', HIGH: 'high card'}


class Card:
    def __init__(self, number, suit):
        self.number = number
        self.suit = suit

    def __str__(self):
        return f'{self.number} {SUIT_NAMES[self.suit]}'

    def __eq__(self, other):
        return self.number == other.number and self.suit == other.suit

    def __hash__(self) -> int:
        return self.number + self.suit * 13

    def give_number(self):
        return self.number

class Quintet:
    def __init__(self, type_of_win, list_of_cards):
        self.type = type_of_win
        list_of_cards.sort(key=Card.give_number)
        self.cards = list_of_cards

    def __str__(self):
        return f'{WIN_NAMES[self.type]} \n{[str(card) for card in self.cards]}'

FULL_SET = [Card(num, suit) for num in range(1, 14) for suit in range(4)]
SUIT_COMBOS = [(a, b) for a in range(4) for b in range(4)]

def best5(hand, table):
    """takes in 5 on table and 2 in hand, returns Quintet of win type & 5 best cards"""
    cards = hand + table
    aces = []
    for card in cards:
        if card.number == 1:
            aces.append(Card(14, card.suit))
    cards += aces
    suits = [card.suit for card in cards]
    numbers = [card.number for card in cards]

    # checks for flush and flush variants (royal, straight flushes)
    for flush_suit in range(4):
        if sum([suits[i] == flush_suit for i in range(7)]) >= 5:
            flushed_numbers = sorted([numbers[i] for i, suit in enumerate(suits) if suit == flush_suit])
            straighted, best_5_num = is_straight(flushed_numbers)
            if straighted:
                best_5 = [Card(number, flush_suit) for number in best_5_num]
                return Quintet(ROYAL_FLUSH, best_5) if best_5[-1].number == 14 else Quintet(STRAIGHT_FLUSH, best_5)
            length_flushed = len(flushed_numbers)
            return Quintet(FLUSH, [Card(1 if flushed_number == 14 else flushed_number, flush_suit) for flushed_number in flushed_numbers[:-6:-1]])

    # checking for duplicates
    pairs = []
    threes = []
    for test_num in range(2, 15):
        test_num_appearances = numbers.count(test_num)
        if test_num_appearances == 2:
            pairs.append(test_num)
        elif test_num_appearances == 3:
            threes.append(test_num)
        elif test_num_appearances == 4:
            highest_num = choose_highest([num for num in numbers if num != test_num])[0]
            highest_suit = suits[numbers.index(highest_num)]
            return Quintet(FOUR_OF_A_KIND, [Card(test_num, suit) for suit in range(4)] + [Card(highest_num, highest_suit)])

    # full house
    if threes and pairs:
        highest_trip, highest_pair = sorted(threes)[-1], sorted(pairs)[-1]
        return Quintet(FULL_HOUSE, [card for card in cards if card.number == highest_trip or card.number == highest_pair])
    if len(threes) == 2:
        highest_trip, highest_pair = sorted(threes)[-1], sorted(threes)[-2]
        triplet = [card for card in cards if card.number == highest_trip]
        double = [card for card in cards if card.number == highest_pair][:2]
        return Quintet(FULL_HOUSE, triplet + double)

    # straight
    is_not_not_straight, best_5 = is_straight(numbers)
    if is_not_not_straight:
        straight_cards = []
        for number in best_5:
            straight_cards.append([card for card in cards if card.number == number][0])
        return Quintet(STRAIGHT, straight_cards)

    # normal trip
    if threes:
        highest_three = sorted(threes)[-1]
        highest_remaining_two = choose_highest([num for num in numbers if num != highest_three], 2)
        return Quintet(THREE, [card for card in cards if card.number in [highest_three] + highest_remaining_two])
        # don't have to worry about duplicates in the highest_remaining_two, because if there were it would've been
        # a full house

    # two pair
    if len(pairs) >= 2:
        pair_nums = sorted(pairs)[-2:]
        highest_remaining_num = choose_highest([num for num in numbers if num not in pair_nums])[0]
        highest_remaining_suit = suits[numbers.index(highest_remaining_num)]
        highest_remaining = [Card(highest_remaining_num, highest_remaining_suit)]
        return Quintet(TWO_PAIR, [card for card in cards if card.number in pair_nums] + highest_remaining)

    # pair
    if pairs:
        highest_remaining_nums = choose_highest([num for num in numbers if num != pairs[0]], 3)
        return Quintet(PAIR, [card for card in cards if card.number in (pairs + highest_remaining_nums)])

    # high card
    highest_nums = choose_highest(numbers, 5)
    return Quintet(HIGH, [card for card in cards if card.number in highest_nums])

def better_hands_after_5(your_hand, table):
    """after all 5 cards are out, checks to see how many hands are better than yours"""
    # your_hand is your hand, table is table, other_hands is while recursive, finds better hands
    your_quintet = best5(your_hand, table)
    used_cards = your_hand + table
    better_hands = []
    # check all the hands that are greater than yours, then same but higher number
    if your_quintet.type != HIGH:
        # means there are probably fewer hands better than yours, than higher
        if your_quintet.type < ROYAL_FLUSH:
            # looks for royal flush potential
            for flush_suit in range(4):
                royal_flush_cards = [Card(num, flush_suit) for num in [10, 11, 12, 13, 1]]
                royal_flush_present = [card in royal_flush_cards for card in table]
                if sum(royal_flush_present) == 3:
                    # only having the remaining 2 cards can you complete the royal flush
                    [add_hand_if_valid(better_hands, [card for card in royal_flush_cards if card not in table])]
                elif sum(royal_flush_present) == 4:
                    # hands that can beat you are hands with the royal flush completing card
                    royal_card = [card for card in royal_flush_cards if card not in table][0]
                    used_cards = your_hand + table + royal_flush_cards
                    [add_hand_if_valid(better_hands, [royal_card, card]) for card in FULL_SET if card not in used_cards]
                elif sum(royal_flush_present) == 5:
                    # everyone has a royal flush so you're all the same
                    return []

        # sets up for checking for flushes later
        can_flush, flush_suit, flush_cards = check_flush_potential(table)

        # looking for straight flushes
        if your_quintet.type < STRAIGHT_FLUSH and your_quintet.type > FLUSH and can_flush:
            # if your hand is worse than flush, doesn't check here, since will be included in flush anyways
            # if your hand is a flush, then that's a different matter. will be checked with the flush checks
            cards_for_straight = check_straight_potential(flush_cards)
            [add_hand_if_valid(better_hands, [Card(num_pair[0], flush_suit), Card(num_pair[1], flush_suit)]) for num_pair in cards_for_straight]

        # saving nums & dups for later for later
        table_nums = [card.number for card in table]
        # if four of a kind is on the table, no better hands from here on out
        if sum([table_nums.count(num) == 4 for num in set(table_nums)]) > 0:
            """HAVE TO ACCOUNT FOR HIGHER CARDS TO SEE WHO WINS"""
            return better_hands

        # saves triples and doubles that are on the table, for further checking
        table_triple = [num for num in set(table_nums) if table_nums.count(num) == 3]
        table_double = [num for num in set(table_nums) if table_nums.count(num) == 2]

        # looking for four of a kind
        if your_quintet.type < FOUR_OF_A_KIND:
            # if your hand is worse than four of a kind, look for four of a kind
            if table_triple:
                # if there's a triple on the board, add hands which can have the last card
                for triple_num in table_triple:
                    required_card = Card(triple_num, 6 - sum([card.suit for card in table if card.number == triple_num]))
                    [add_hand_if_valid(better_hands, [required_card, Card(num, suit)]) for num in range(1, 14) for suit in range(4) if Card(num, suit) not in used_cards and Card(num, suit) != required_card]
            if table_double:
                # if there's a double on the board
                for double_num in table_double:
                    used_suits = [card.suit for card in table if card.number == double_num]
                    remaining_suits = [suit for suit in range(4) if suit not in used_suits]
                    add_hand_if_valid(better_hands, [Card(double_num, remaining_suits[0]), Card(double_num, remaining_suits[1])])
    
    return better_hands

# save for straights
# better_hands += [(Card(num_pair[0], suit_pair[0]), Card(num_pair[1], suit_pair[1])) for num_pair in cards_for_straight for suit_pair in SUIT_COMBOS if Card(num_pair[0], suit_pair[0]) not in used_cards and Card(num_pair[1], suit_pair[1]) not in used_cards and suit_pair[0] != suit_pair[1]]

"""HELPER FUNCTIONS"""
def is_straight(numbers):
    rev_sort = list(set(sorted(numbers)))[::-1]
    differences_of_one = [rev_sort[i] - rev_sort[i+1] == 1 for i in range(len(rev_sort) - 1)]
    for i in range(len(differences_of_one) - 3):
        if sum([differences_of_one[i+j] == 1 for j in range(4)]) == 4:
            if i == 0:
                return True, rev_sort[i+4::-1]
            return True, rev_sort[i + 4:i-1:-1]
    return False, None

def choose_highest(choices, n=1):
    """chooses the highest n within choices (list of card numbers)"""
    return sorted(choices)[len(choices)-n:]

def check_flush_potential(table):
    """given 5 cards on the table, checks for flush potential, and if so, gives card of that suit"""
    for flush_suit in range(4):
        suited_cards = [card for card in table if card.suit == flush_suit]
        if len(suited_cards) >= 3:
            return True, flush_suit, suited_cards
    return False, None, None

def check_straight_potential(table):
    """given cards on the table, check for missing 0-2 cards to straight, and if so, gives pairs of nums that complete it"""
    # sorts it in descending order
    numbers = sorted([card.number for card in table])[::-1]
    winning_nums = []
    if 1 in numbers:
        numbers.insert(0, 14)
    for straight_start in range(1, 11):
        counted_in_straight = [num >= straight_start and num <= straight_start + 4 for num in numbers]
        if sum(counted_in_straight) == 3:
            existing_straighters = [numbers[i] for i, counted in enumerate(counted_in_straight) if counted]
            winning_pair = tuple(sorted([(1 if num == 14 else num) for num in range(straight_start, straight_start+5) if num not in existing_straighters]))
            if winning_pair not in winning_nums:
                winning_nums.append(winning_pair)
        elif sum(counted_in_straight) == 4:
            existing_straighters = [numbers[i] for i, counted in enumerate(counted_in_straight) if counted]
            winning_number = [(1 if num == 14 else num) for num in range(straight_start, straight_start+5) if num not in existing_straighters][0]
            winning_nums += [tuple(sorted((winning_number, i))) for i in range(1, 14) if (i < straight_start or i > straight_start + 4) and tuple(sorted((winning_number, i))) not in winning_nums]
    return winning_nums

def add_hand_if_valid(better_hands, pair_of_cards):
    """helper function to add pair_of_cards (list). ensured added to better_hands correctly and avoids duplicates"""
    # NOTE that it doesn't check if the pair of cards is already used
    tuple_to_add = tuple(sorted(pair_of_cards, key=hash))
    if tuple_to_add in better_hands:
        return
    better_hands.append(tuple_to_add)

pair_num = lambda pair : 52 * hash(pair[0]) + hash(pair[1])

if __name__ == '__main__':
    print()
    hand_test = [Card(11, CLUB), Card(9, HEART)]
    table_test = [Card(10, DIAM), Card(8, HEART), Card(10, CLUB), Card(12, HEART), Card(13, HEART)]
    used_cards = hand_test + table_test
    goodest_hand = best5(hand_test, table_test)
    print(goodest_hand)
    better_hands = better_hands_after_5(hand_test, table_test)
    better_hands.sort(key=pair_num)
    for hand in better_hands:
        print(f'{hand[0]}, {hand[1]}')
    print(f'No Duplicates?       {len(better_hands) == len(set(better_hands))}')
    print(f'Used used cards?     {sum([card in card_pair for card in used_cards for card_pair in better_hands]) != 0}')
    print(f'No. of better hands: {len(better_hands)}')
    print(f'Total no. of hands:  {45*44//2}')
    print()
