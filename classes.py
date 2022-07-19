from itertools import permutations
import datetime

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
    def __init__(self, type_of_win, list_of_cards, defining_num):
        self.type = type_of_win
        list_of_cards.sort(key=Card.give_number)
        self.cards = list_of_cards
        self.defining_num = defining_num

    def __str__(self):
        return f'{WIN_NAMES[self.type]} \n{[str(card) for card in self.cards]} with {self.defining_num} being defining.'

FULL_SET = [Card(num, suit) for num in range(1, 14) for suit in range(4)]
SUIT_COMBOS = list(permutations([0, 1, 2, 3], 2))

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
                return Quintet(ROYAL_FLUSH, best_5, 14) if best_5[-1].number == 14 else Quintet(STRAIGHT_FLUSH, best_5, best_5_num[-1])
            return Quintet(FLUSH, [Card(flushed_number, flush_suit) for flushed_number in flushed_numbers[:-6:-1]], flushed_numbers[-1])

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
            return Quintet(FOUR_OF_A_KIND, [Card(test_num, suit) for suit in range(4)] + [Card(highest_num, highest_suit)], test_num)

    # full house
    if threes and pairs:
        highest_trip, highest_pair = sorted(threes)[-1], sorted(pairs)[-1]
        return Quintet(FULL_HOUSE, [card for card in cards if card.number == highest_trip or card.number == highest_pair], highest_trip)
    if len(threes) == 2:
        highest_trip, highest_pair = sorted(threes)[-1], sorted(threes)[-2]
        triplet = [card for card in cards if card.number == highest_trip]
        double = [card for card in cards if card.number == highest_pair][:2]
        return Quintet(FULL_HOUSE, triplet + double, highest_trip)

    # straight
    is_not_not_straight, best_5 = is_straight(numbers)
    if is_not_not_straight:
        straight_cards = []
        for number in best_5:
            straight_cards.append([card for card in cards if card.number == number][0])
        return Quintet(STRAIGHT, straight_cards, best_5[-1])

    # normal trip
    if threes:
        highest_three = sorted(threes)[-1]
        highest_remaining_two = choose_highest([num for num in numbers if num != highest_three], 2)
        return Quintet(THREE, [card for card in cards if card.number in [highest_three] + highest_remaining_two], highest_three)
        # don't have to worry about duplicates in the highest_remaining_two, because if there were it would've been
        # a full house

    # two pair
    if len(pairs) >= 2:
        pair_nums = sorted(pairs)[-2:]
        highest_remaining_num = choose_highest([num for num in numbers if num not in pair_nums])[0]
        highest_remaining_suit = suits[numbers.index(highest_remaining_num)]
        highest_remaining = [Card(highest_remaining_num, highest_remaining_suit)]
        return Quintet(TWO_PAIR, [card for card in cards if card.number in pair_nums] + highest_remaining, pair_nums[-1])

    # pair
    if pairs:
        highest_remaining_nums = choose_highest([num for num in numbers if num != pairs[0]], 3)
        return Quintet(PAIR, [card for card in cards if card.number in (pairs + highest_remaining_nums)], pairs[0])

    # high card
    highest_nums = choose_highest(numbers, 5)
    return Quintet(HIGH, [card for card in cards if card.number in highest_nums], max(highest_nums))

def better_hands_after_5(your_hand, table):
    """after all 5 cards are out, checks to see how many hands are better than yours"""
    # your_hand is your hand, table is table, other_hands is while recursive, finds better hands
    your_quintet = best5(your_hand, table)
    used_cards = your_hand + table
    unused_cards = [card for card in FULL_SET if card not in used_cards]
    better_hands = []
    # check all the hands that are greater than yours, then same but higher number

    # sets up for checking for flushes later
    can_flush, flush_suit, suited_table_cards = check_flush_potential(table)

    # doesn't have to look for royal flush, since it's just a rly good straight flush and included below
    # looking for straight flushes
    if your_quintet.type < STRAIGHT_FLUSH and your_quintet.type > FLUSH and can_flush:
        # if your hand is worse than flush, doesn't check here, since will be included in flush anyways
        # if your hand is a flush, then that's a different matter. will be checked with the flush checks
        cards_for_straight = check_straight_potential(suited_table_cards)
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
    table_single = [num for num in set(table_nums) if table_nums.count(num) == 1]

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

    # looking for full house
    if your_quintet.type < FULL_HOUSE:
        if table_triple:
            # if triple on table, only need a double to win
            # first check for pairs with remaining two table cards
            for table_card in table:
                if table_card.number == table_triple[0]:
                    continue
                for pair_suit in [suit for suit in range(4) if suit != table_card.suit]:
                    pair_card = Card(table_card.number, pair_suit)
                    if pair_card in used_cards:
                        continue
                    [add_hand_if_valid(better_hands, [pair_card, Card(num, suit)]) for num in range(1, 14) for suit in range(4) if Card(num, suit) not in used_cards]
            # then check for pocket pairs
            for num in range(1, 14):
                if num == table_triple:
                    continue
                [add_hand_if_valid(better_hands, [Card(num, suits[0]), Card(num, suits[1])]) for suits in SUIT_COMBOS if Card(num, suits[0]) not in used_cards and Card(num, suits[1]) not in used_cards]
        if len(table_double) == 1:
            # if one double on table, need one of double and another single
            required_num = table_double[0]
            used_suits = [card.suit for card in table if card.number == required_num]
            remaining_suits = [suit for suit in range(4) if suit not in used_suits]
            for double_suit in remaining_suits:
                required_double = Card(required_num, double_suit)
                if required_double in used_cards:
                    continue
                usable_nums = [card.number for card in table if card.number != required_num]
                [add_hand_if_valid(better_hands, [required_double, Card(num, suit)]) for num in usable_nums for suit in range(4) if Card(num, suit) not in used_cards]
        elif len(table_double) == 2:
            # if two doubles on table, only need one more card to win...
            for required_num in table_double:
                used_suits = [card.suit for card in table if card.number == required_num]
                remaining_suits = [suit for suit in range(4) if suit not in used_suits]
                for required_suit in remaining_suits:
                    required_card = Card(required_num, required_suit)
                    if required_card in used_cards:
                        continue
                    [add_hand_if_valid(better_hands, [required_card, Card(num, suit)]) for num in range(1,14) for suit in range(4) if Card(num, suit) not in used_cards]
            # ... or if pocket pair with remaining card
            remaining_num = [card for card in table if card.number not in table_double][0].number
            [add_hand_if_valid(better_hands, [Card(remaining_num, suits[0]), Card(remaining_num, suits[1])]) for suits in SUIT_COMBOS if Card(remaining_num, suits[0]) not in used_cards and Card(remaining_num, suits[1]) not in used_cards]

    # looking for flushes
    if your_quintet.type < FLUSH:
        # uses check_flush_potential from earlier
        if can_flush:
            flushed_table_nums = [card.number for card in suited_table_cards]
            flushed_hand = [card.number for card in your_hand if card.suit == flush_suit]
            
            if len(suited_table_cards) == 3:
                # 3 flushed on table
                usable_nums = [i for i in range(1, 14) if i not in flushed_table_nums and i not in flushed_hand]
                potential_better_pairs = permutations(usable_nums, 2)
                [add_hand_if_valid(better_hands, [Card(nums[0], flush_suit), Card(nums[1], flush_suit)]) for nums in potential_better_pairs]
            
            elif len(suited_table_cards) == 4:
                # 4 flushed on table
                usable_nums = [i for i in range(1, 14) if i not in flushed_table_nums and i not in flushed_hand]
                for usable_num in usable_nums:
                    required_card = Card(usable_num, flush_suit)
                    [add_hand_if_valid(better_hands, [required_card, Card(num, other_suit)]) for num in range(1, 14) for other_suit in range(4) if Card(num, other_suit) not in used_cards and Card(num, flush_suit) != required_card]
            # no need to account for 5 flushed on table here, since it counts as everyone having a flush. and that's a different issue.

    # looking for straights
    if your_quintet.type < STRAIGHT:
        # checks for straight potential
        winning_nums = check_straight_potential(table)
        [add_hand_if_valid(better_hands, [Card(num_pair[0], suit_pair[0]), Card(num_pair[1], suit_pair[1])]) for num_pair in winning_nums for suit_pair in SUIT_COMBOS if Card(num_pair[0], suit_pair[0]) not in used_cards and Card(num_pair[1], suit_pair[1]) not in used_cards]

    # looking for triples
    if your_quintet.type < THREE:
        # doesn't care about table triples, since that means everyone has a triple, and that's a different case

        # checks for completing a double. doesn't matter if you try to add a full house accidentally.
        for double_num in table_double:
            for trip_completer_suit in range(4):
                trip_completer = Card(double_num, trip_completer_suit)
                if trip_completer in used_cards:
                    continue
                [add_hand_if_valid(better_hands, [trip_completer, other_card]) for other_card in unused_cards]
        
        # checks for pocket pairs with a single card in the table
        for single_num in table_single:
            remaining_suits = [0, 1, 2, 3]
            remaining_suits.remove([card.suit for card in used_cards if card.number == single_num][0])
            remaining_combos = permutations(remaining_suits, 2)
            [add_hand_if_valid(better_hands, [Card(single_num, suits[0]), Card(single_num, suits[1])]) for suits in remaining_combos]

    # looking for twopairs
    if your_quintet.type < TWO_PAIR:
        # doesn't care about table triples, since if there was, you'd already have a trip, whcih is better than twopair
        # table double must only have 1 thing, since if there were 2, you'd already have a twopair
        if table_double:
            # you only need a pair from one of the singles...
            required_num = table_double[0]
            remaining_suits = [0, 1, 2, 3]
            [remaining_suits.remove(card.suit) for card in used_cards if card.number == required_num]
            [add_hand_if_valid(better_hands, [Card(required_num, remaining_suit), other_card]) for remaining_suit in remaining_suits for other_card in unused_cards]

            # ... or a pocket pair
            potential_pocket_nums = list(range(1, 14))
            potential_pocket_nums.remove(required_num)
            [potential_pocket_nums.remove(num) for num in table_single]
            [add_hand_if_valid(better_hands, [Card(num, suits[0]), Card(num, suits[1])]) for num in potential_pocket_nums for suits in SUIT_COMBOS if Card(num, suits[0]) not in used_cards and Card(num, suits[1]) not in used_cards]

        else:
            # then the table is full of singles, and you've just got to match two of them
            winning_hands_nums = list(permutations([card.number for card in table], 2))
            [add_hand_if_valid(better_hands, [Card(pair_nums[0], suits[0]), Card(pair_nums[1], suits[1])]) for pair_nums in winning_hands_nums for suits in SUIT_COMBOS if Card(pair_nums[0], suits[0]) not in used_cards and Card(pair_nums[1], suits[1]) not in used_cards]

    # looking for pairs
    if your_quintet.type < PAIR:
        # the table must be full of singles, since if there was a pair on the table, you'd have a pair
        for sing_num in table_single:
            remaining_suits = [0, 1, 2, 3]
            [remaining_suits.remove(card.suit) for card in used_cards if card.number == sing_num]
            [add_hand_if_valid(better_hands, [Card(sing_num, sing_suit), other_card]) for sing_suit in remaining_suits for other_card in unused_cards]

    """NOW LOOKING FOR SAME TIER BUT MILDLY BETTER PAIRS"""
    # looks from worse to best, because chances are you've got a bad hand rather than good.

    if your_quintet.type == STRAIGHT_FLUSH:
        # first looks for your highest card
        your_nums = [card.number for card in your_quintet.cards]
        your_highest = max(your_nums)

        # since already 3 of same suit on table for your straight flush, any other straight flush will be of same suit
        flush_suit = your_quintet.cards[0].suit

        # then checks for potential straights with table cards of flush suit
        flushed_table_cards = [card for card in table if card.suit == flush_suit]
        max_flushed_table_num = max([card.number for card in flushed_table_cards])
        straight_num_pairs = check_straight_potential(flushed_table_cards)
        better_num_pairs = [pair for pair in straight_num_pairs if max(max(pair), max_flushed_table_num) > your_highest]

        # now we just add the better pairs back, but as cards of flush suit
        [add_hand_if_valid(better_hands, [Card(num_pair[0], flush_suit), Card(num_pair[1], flush_suit)]) for num_pair in better_num_pairs]

    return better_hands

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
    numbers = sorted(list(set([card.number for card in table])))[::-1]
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
    if tuple_to_add in better_hands or pair_of_cards[0] == pair_of_cards[1]: # tuple_to_add in better_hands or 
        return
    better_hands.append(tuple_to_add)

pair_num = lambda pair : 52 * hash(pair[0]) + hash(pair[1])

"""---------------------------------------------------------------------------------------------------------------------"""

if __name__ == '__main__':
    print()
    hand_test = [Card(8, SPADE), Card(10, HEART)]
    table_test = [Card(3, HEART), Card(1, CLUB), Card(11, CLUB), Card(8, CLUB), Card(12, HEART)]
    used_cards = hand_test + table_test

    start_time = datetime.datetime.now()
    goodest_hand = best5(hand_test, table_test)
    end_time = datetime.datetime.now()
    print(f'\nTime to find hand         {end_time-start_time}')

    print(goodest_hand)
    print()
    
    start_time = datetime.datetime.now()
    better_hands = better_hands_after_5(hand_test, table_test)
    end_time = datetime.datetime.now()
    print(f'Time for better hands:    {end_time-start_time}\n')

    # better_hands.sort(key=pair_num)
    for hand in better_hands:
        print(f'{hand[0]}, {hand[1]}')
    print(f'No Duplicates?       {len(better_hands) == len(set(better_hands))}')
    print(f'Used used cards?     {sum([card in card_pair for card in used_cards for card_pair in better_hands]) != 0}')
    print(f'No. of better hands: {len(better_hands)}')
    print(f'Total no. of hands:  {45*44//2}')
    # total_hands = [(Card(num1, suit1), Card(num2, suit2)) for num1 in range(1, 14) for num2 in range(1, 14) for suit1 in range(4) for suit2 in range(4) if Card(num1, suit1) != Card(num2, suit2) and Card(num1, suit1) not in used_cards and Card(num2, suit2) not in used_cards]
    # print(len(total_hands)) # note that you should divide this by 2 because this one double counts swapsies
    print()
