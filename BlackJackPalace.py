import tkinter as tk
import random
import time
from tkinter import messagebox
import math
import json

'''
NOTE: To run, please make sure you have tkinter installed, and make sure you have a modern version of Python 3.
This game is compatible with Python 3.6 or newer on MacOS.
Run with: python3 PromptingProject_BlackJack.py 
'''

# Card class
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.value = self.get_value()

    def get_value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)

    def __str__(self):
        return f"{self.rank} of {self.suit}"

# Deck class
class Deck:
    def __init__(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(self.cards)

    def deal_card(self):
        return self.cards.pop()

# Player class
class Player:
    def __init__(self, name, chips=100, wins=0, badges=None, achievements=None):
        self.name = name
        self.hand = []
        self.chips = chips
        self.bet = 0
        self.wins = wins
        self.badges = badges if badges is not None else []
        self.achievements = achievements if achievements is not None else []
        self.doubled_down = False
        self.insurance_bet = 0

    def place_bet(self, amount):
        if amount <= self.chips:
            self.bet = amount
            self.chips -= amount
            return True
        return False

    def win_bet(self, is_blackjack=False):
        if is_blackjack:
            # Blackjack pays 3:2 (1.5x the bet)
            self.chips += int(2.5 * self.bet)
        else:
            # Regular win pays 1:1 (2x the bet total)
            self.chips += 2 * self.bet
        self.bet = 0

    def push_bet(self):
        self.chips += self.bet
        self.bet = 0

    def double_down(self):
        """Double the bet and mark player as doubled down"""
        if self.chips >= self.bet:
            self.chips -= self.bet
            self.bet *= 2
            self.doubled_down = True
            return True
        return False

    def reset_hand(self):
        self.hand = []
        self.doubled_down = False

# Dealer class
class Dealer(Player):
    def __init__(self):
        super().__init__('Dealer')

    def should_hit(self):
        return self.get_hand_value() < 17

    def get_hand_value(self):
        value = sum(card.value for card in self.hand)
        aces = sum(1 for card in self.hand if card.rank == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

class BlackjackGame:
    def __init__(self, root):
        self.root = root
        self.root.title("🎀 BlackJack Palace 👑✨")
        self.root.configure(bg="#ffe6f0")
        self.leaderboard_file = "leaderboard.json"
        self.player_stats = self.load_player_stats()
        self.reset_full_game()
        self.setup_start_screen()

    def reset_full_game(self):
        self.deck = Deck()
        self.players = []
        self.dealer = Dealer()
        self.current_player_idx = 0
        self.timer_id = None
        self.time_remaining = 15

    def style_button(self, button):
        button.configure(bg="yellow", fg="#9933cc", font=("Comic Sans MS", 12, "bold"),
                          activebackground="#ffcc66", activeforeground="#9933cc",
                          relief="raised", bd=4, highlightbackground="gold")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def setup_start_screen(self):
        self.clear_screen()
        if not hasattr(self, 'card_theme'):
            self.card_theme = 'bow'  # Default to bow if not set
        self.reset_full_game()
        self.title = tk.Label(self.root, text="🎀 Welcome to BlackJack Palace! 👑💖", font=("Comic Sans MS", 28, "bold"), fg="#9933cc", bg="#ffe6f0")
        self.title.pack(pady=30)
        # Customize Cards button (top right)
        self.customize_button = tk.Button(self.root, text="Customize Cards", command=self.show_customize_page)
        self.style_button(self.customize_button)
        self.customize_button.place(relx=1.0, y=10, anchor="ne")
        self.name_label = tk.Label(self.root, text="Enter player names:", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.name_label.pack(pady=10)
        # Two separate entry fields for player names
        self.player1_label = tk.Label(self.root, text="Player 1:", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.player1_label.pack()
        self.player1_entry = tk.Entry(self.root, font=("Comic Sans MS", 12), fg="#9933cc", bg="white")
        self.player1_entry.pack(pady=2)
        self.player2_label = tk.Label(self.root, text="Player 2:", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.player2_label.pack()
        self.player2_entry = tk.Entry(self.root, font=("Comic Sans MS", 12), fg="#9933cc", bg="white")
        self.player2_entry.pack(pady=2)
        self.start_button = tk.Button(self.root, text="Start Game", command=self.start_game)
        self.style_button(self.start_button)
        self.start_button.pack(pady=20)
        # Play Against AI button
        self.ai_button = tk.Button(self.root, text="Play Against AI", command=self.start_game_vs_ai)
        self.style_button(self.ai_button)
        self.ai_button.pack(pady=5)
        # Achievements + Leaderboard button
        self.achievements_button = tk.Button(self.root, text="Achievements + Leaderboard", command=self.show_achievements_leaderboard)
        self.style_button(self.achievements_button)
        self.achievements_button.pack(pady=5)
        # Add Exit button to close the application
        self.exit_button = tk.Button(self.root, text="Exit", command=self.root.quit)
        self.style_button(self.exit_button)
        self.exit_button.pack(pady=5)

    def show_customize_page(self):
        self.clear_screen()
        # Suite label at the top
        suite_names = {'bow': '🎀 The Bow Suite 🎀', 'flower': '🌸 The Flower Suite 🌸', 'ballet': '🩰 The Ballerina Suite 🩰'}
        self.suite_label = tk.Label(self.root, text=f"Current Suite: {suite_names.get(self.card_theme, '🎀 The Bow Suite 🎀')}", font=("Comic Sans MS", 16, "bold"), fg="#9933cc", bg="#ffe6f0")
        self.suite_label.pack(pady=(20, 10))
        label = tk.Label(self.root, text="Choose Your Card Theme!", font=("Comic Sans MS", 20, "bold"), fg="#9933cc", bg="#ffe6f0")
        label.pack(pady=10)
        # Theme buttons
        bow_btn = tk.Button(self.root, text="🎀 The Bow Suite 🎀", command=lambda: self.set_card_theme('bow', update_only=True))
        flower_btn = tk.Button(self.root, text="🌸 The Flower Suite 🌸", command=lambda: self.set_card_theme('flower', update_only=True))
        ballet_btn = tk.Button(self.root, text="🩰 The Ballerina Suite 🩰", command=lambda: self.set_card_theme('ballet', update_only=True))
        for btn in (bow_btn, flower_btn, ballet_btn):
            self.style_button(btn)
            btn.pack(pady=10)
        back_btn = tk.Button(self.root, text="Back", command=self.setup_start_screen)
        self.style_button(back_btn)
        back_btn.pack(pady=30)

    def set_card_theme(self, theme, update_only=False):
        self.card_theme = theme
        if update_only:
            # Just update the suite label
            suite_names = {'bow': '🎀 The Bow Suite 🎀', 'flower': '🌸 The Flower Suite 🌸', 'ballet': '🩰 The Ballerina Suite 🩰'}
            if hasattr(self, 'suite_label'):
                self.suite_label.config(text=f"Current Suite: {suite_names.get(self.card_theme, '🎀 The Bow Suite 🎀')}")
        else:
            self.setup_start_screen()

    def get_theme_emoji(self):
        theme = getattr(self, 'card_theme', 'bow')
        if theme == 'flower':
            return "🌸"
        elif theme == 'ballet':
            return "🩰"
        return "🎀"

    def draw_card_box(self, canvas, card, x, y):
        # Card rectangle
        canvas.create_rectangle(x-40, y-60, x+40, y+60, fill="white", outline="purple", width=3)
        # Theme emoji
        deco = self.get_theme_emoji()
        # Top-left corner
        canvas.create_text(x-32, y-52, text=deco, font=("Comic Sans MS", 12), fill="purple", anchor="nw")
        canvas.create_text(x-25, y-45, text=f"{card.rank}{self.get_card_emoji(card)}", font=("Comic Sans MS", 13, "bold"), fill="purple", anchor="nw")
        # Bottom-right corner
        canvas.create_text(x+32, y+52, text=deco, font=("Comic Sans MS", 12), fill="purple", anchor="se")
        canvas.create_text(x+25, y+45, text=f"{card.rank}{self.get_card_emoji(card)}", font=("Comic Sans MS", 13, "bold"), fill="purple", anchor="se")
        # Center: for face cards, show emoji; for number cards, show suit
        if card.rank in ['J', 'Q', 'K', 'A']:
            center_text = self.get_card_emoji(card)
        else:
            center_text = self.get_card_emoji(card)[-1]  # just the suit emoji
        canvas.create_text(x, y, text=center_text, font=("Comic Sans MS", 28, "bold"), fill="purple")

    def start_game(self):
        name1 = self.player1_entry.get().strip()
        name2 = self.player2_entry.get().strip()
        # Use persistent player objects
        self.players = [self.get_or_create_player(name1), self.get_or_create_player(name2)] if name1 and name2 else []
        if not self.players or len(self.players) != 2:
            messagebox.showerror("Error", "Please enter both player names.")
            return
        self.play_round()

    def start_game_vs_ai(self):
        name1 = self.player1_entry.get().strip()
        if not name1:
            messagebox.showerror("Error", "Please enter your name for Player 1.")
            return
        self.players = [self.get_or_create_player(name1), self.AIPlayer(self)]
        self.vs_ai_mode = True
        self.play_round()

    def play_round(self):
        self.clear_screen()
        self.deck = Deck()
        self.dealer.reset_hand()
        for player in self.players:
            player.reset_hand()
        self.animate_shuffle()

    def animate_shuffle(self):
        self.title = tk.Label(self.root, text="🎀 Shuffling the deck... 👑", font=("Comic Sans MS", 24, "bold"), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=30)
        self.root.update()
        for _ in range(10):
            shuffle_label = tk.Label(self.root, text="✨✨✨", font=("Comic Sans MS", 20), bg="#ffe6f0", fg="purple")
            shuffle_label.pack()
            self.root.update()
            time.sleep(0.2)
            shuffle_label.destroy()
        self.bet_phase()

    def bet_phase(self):
        self.clear_screen()
        self.bet_frame = tk.Frame(self.root, bg="#ffe6f0")
        self.bet_frame.pack(pady=10)
        player = self.players[self.current_player_idx]
        if hasattr(player, 'is_ai') and player.is_ai:
            # AI places bet automatically
            player.place_bet()
            self.current_player_idx += 1
            if self.current_player_idx >= len(self.players):
                self.deal_initial_cards()
            else:
                self.bet_phase()
            return
        self.bet_label = tk.Label(self.bet_frame, text=f"{player.name}, place your bet 💰 (Chips: {player.chips}):", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.bet_label.pack()
        self.bet_entry = tk.Entry(self.bet_frame, font=("Comic Sans MS", 12), fg="#9933cc", bg="white")
        self.bet_entry.pack()
        self.bet_button = tk.Button(self.bet_frame, text="Place Bet", command=self.place_bet)
        self.style_button(self.bet_button)
        self.bet_button.pack(pady=5)

    def place_bet(self):
        try:
            amount = int(self.bet_entry.get())
            player = self.players[self.current_player_idx]
            if amount <= 0 or not player.place_bet(amount):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Invalid bet amount.")
            return
        self.current_player_idx += 1
        if self.current_player_idx >= len(self.players):
            self.deal_initial_cards()
        else:
            self.bet_phase()

    def deal_initial_cards(self):
        for player in self.players:
            player.hand.append(self.deck.deal_card())
            player.hand.append(self.deck.deal_card())
        self.dealer.hand.append(self.deck.deal_card())
        self.dealer.hand.append(self.deck.deal_card())
        self.current_player_idx = 0
        
        # Check for dealer Ace (offer insurance)
        if self.dealer.hand[0].rank == 'A':
            self.offer_insurance()
        
        # Check for natural blackjacks before player turns
        if self.check_natural_blackjacks():
            return  # Round ends early due to natural blackjacks
        
        self.play_player_turn()

    def offer_insurance(self):
        """Offer insurance when dealer shows an Ace"""
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Insurance Offered! 🎀", font=("Comic Sans MS", 20, "bold"), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        
        info_label = tk.Label(self.root, text="Dealer shows an Ace. Would you like insurance?", bg="#ffe6f0", font=("Comic Sans MS", 14), fg="#9933cc")
        info_label.pack(pady=5)
        
        info_label2 = tk.Label(self.root, text="Insurance pays 2:1 if dealer has blackjack", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        info_label2.pack(pady=5)
        
        # Show dealer's upcard
        canvas = tk.Canvas(self.root, bg="#ffe6f0", width=300, height=150, highlightthickness=0)
        canvas.pack(pady=10)
        self.draw_card_box(canvas, self.dealer.hand[0], 150, 75)
        
        self.insurance_player_idx = 0
        self.process_insurance_for_player()

    def process_insurance_for_player(self):
        """Process insurance decision for current player"""
        if self.insurance_player_idx >= len(self.players):
            # All players have decided, continue with game
            return
        
        player = self.players[self.insurance_player_idx]
        
        # Skip AI players for insurance (they don't take insurance)
        if hasattr(player, 'is_ai') and player.is_ai:
            self.insurance_player_idx += 1
            self.process_insurance_for_player()
            return
        
        # Check if player can afford insurance (half their bet)
        insurance_cost = player.bet // 2
        if player.chips < insurance_cost:
            # Can't afford insurance, skip
            self.insurance_player_idx += 1
            self.process_insurance_for_player()
            return
        
        # Ask player for insurance
        player_label = tk.Label(self.root, text=f"{player.name}: Insurance costs {insurance_cost} chips", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        player_label.pack(pady=5)
        
        button_frame = tk.Frame(self.root, bg="#ffe6f0")
        button_frame.pack(pady=10)
        
        yes_btn = tk.Button(button_frame, text="Take Insurance", command=lambda: self.take_insurance(player, insurance_cost))
        self.style_button(yes_btn)
        yes_btn.pack(side=tk.LEFT, padx=10)
        
        no_btn = tk.Button(button_frame, text="No Insurance", command=self.decline_insurance)
        self.style_button(no_btn)
        no_btn.pack(side=tk.LEFT, padx=10)

    def take_insurance(self, player, cost):
        """Player takes insurance"""
        player.chips -= cost
        player.insurance_bet = cost
        self.insurance_player_idx += 1
        self.clear_insurance_ui()
        self.process_insurance_for_player()

    def decline_insurance(self):
        """Player declines insurance"""
        player = self.players[self.insurance_player_idx]
        player.insurance_bet = 0
        self.insurance_player_idx += 1
        self.clear_insurance_ui()
        self.process_insurance_for_player()

    def clear_insurance_ui(self):
        """Clear insurance-related UI elements"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.Label):
                if widget != self.title:  # Keep the title
                    widget.destroy()

    def check_natural_blackjacks(self):
        """Check for natural blackjacks and handle them. Returns True if round should end."""
        dealer_blackjack = len(self.dealer.hand) == 2 and self.dealer.get_hand_value() == 21
        player_blackjacks = []
        
        # Check each player for blackjack
        for player in self.players:
            if len(player.hand) == 2 and self.calculate_hand_value(player.hand) == 21:
                player_blackjacks.append(player)
        
        # If no blackjacks, continue normal play
        if not dealer_blackjack and not player_blackjacks:
            return False
        
        # Handle natural blackjack scenarios
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Natural Blackjack! 🎀", font=("Comic Sans MS", 20, "bold"), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        
        # Show all hands
        canvas = tk.Canvas(self.root, bg="#ffe6f0", width=900, height=600, highlightthickness=0)
        canvas.pack()
        
        # Show dealer's full hand
        canvas.create_text(110, 50, text="Dealer's Hand:", font=("Comic Sans MS", 12, "bold"), fill="#9933cc", anchor="w")
        for idx, card in enumerate(self.dealer.hand):
            x = 150 + idx * 150
            self.draw_card_box(canvas, card, x, 120)
        
        # Show player hands
        y_start = 280
        y_step = 160
        for player_idx, player in enumerate(self.players):
            y_pos = y_start + player_idx * y_step
            canvas.create_text(110, y_pos - 80, text=f"{player.name}'s Hand:", font=("Comic Sans MS", 12, "bold"), fill="#9933cc", anchor="w")
            for idx, card in enumerate(player.hand):
                x = 150 + idx * 150
                self.draw_card_box(canvas, card, x, y_pos)
        
        result_text = f"Dealer Value: {self.dealer.get_hand_value()}\n"
        
        # Process results
        for player in self.players:
            player_value = self.calculate_hand_value(player.hand)
            player_has_blackjack = player in player_blackjacks
            
            if dealer_blackjack and player_has_blackjack:
                # Both have blackjack - push
                player.push_bet()
                result_text += f"{player.name}: Blackjack vs Blackjack - Push!\n"
            elif player_has_blackjack and not dealer_blackjack:
                # Player blackjack wins
                player.win_bet(is_blackjack=True)
                player.wins += 1
                result_text += f"{player.name}: Natural Blackjack! Pays 3:2! 🎉\n"
            elif dealer_blackjack and not player_has_blackjack:
                # Dealer blackjack, player loses
                result_text += f"{player.name}: Dealer Blackjack - You lose.\n"
            
            self.update_player_stats(player)
        
        # Show results
        result_label = tk.Label(self.root, text=result_text, bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        result_label.pack(pady=10)
        
        # Continue to next round or end game
        self.root.after(3000, self.check_game_over)
        return True

    def get_card_emoji(self, card):
        suit_emojis = {
            'Hearts': '❤️',
            'Diamonds': '💎',
            'Clubs': '♣️',
            'Spades': '♠️'
        }
        rank_emojis = {
            'J': '🧑',
            'Q': '👸',
            'K': '🤴',
            'A': '🅰️'
        }
        bottom = ''
        if card.rank in rank_emojis:
            bottom += rank_emojis[card.rank]
        bottom += suit_emojis.get(card.suit, '')
        return bottom

    def play_player_turn(self):
        self.clear_screen()
        player = self.players[self.current_player_idx]
        if hasattr(self, 'vs_ai_mode') and self.vs_ai_mode:
            title_text = f"🎀 {player.name}'s Turn 👸 (Chips: {player.chips}) [You vs AI]"
        else:
            title_text = f"🎀 {player.name}'s Turn 👸 (Chips: {player.chips})"
        self.title = tk.Label(self.root, text=title_text, font=("Comic Sans MS", 16), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        dealer_upcard_text = "Dealer's Upcard:"
        self.dealer_label = tk.Label(self.root, text=dealer_upcard_text, bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.dealer_label.pack(pady=5)
        self.canvas = tk.Canvas(self.root, bg="#ffe6f0", width=900, height=400, highlightthickness=0)
        self.canvas.pack()
        
        # Draw dealer upcard only (hide hole card)
        self.draw_card_box(self.canvas, self.dealer.hand[0], 150, 80)
        
        # Draw hole card face down
        self.draw_hole_card(self.canvas, 300, 80)
        
        # Draw player hand
        self.hand_label = tk.Label(self.root, text="Your Hand:" if not (hasattr(player, 'is_ai') and player.is_ai) else "AI's Hand:", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.hand_label.pack()
        for idx, card in enumerate(player.hand):
            x = 150 + idx * 150
            self.draw_card_box(self.canvas, card, x, 250)
        self.value_label = tk.Label(self.root, text=f"Hand Value: {self.calculate_hand_value(player.hand)}", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.value_label.pack(pady=5)
        if hasattr(player, 'is_ai') and player.is_ai:
            # AI turn: auto hit/stand
            self.root.after(2000, self.ai_play_turn)
            return
        
        # Create button frame for better layout
        button_frame = tk.Frame(self.root, bg="#ffe6f0")
        button_frame.pack(pady=20)
        
        self.hit_button = tk.Button(button_frame, text="Hit", command=self.hit)
        self.style_button(self.hit_button)
        self.hit_button.pack(side=tk.LEFT, padx=10)
        
        self.stand_button = tk.Button(button_frame, text="Stand", command=self.stand)
        self.style_button(self.stand_button)
        self.stand_button.pack(side=tk.LEFT, padx=10)
        
        # Double Down button (only available with 2 cards and sufficient chips)
        if len(player.hand) == 2 and player.chips >= player.bet and not getattr(player, 'doubled_down', False):
            self.double_button = tk.Button(button_frame, text="Double Down", command=self.double_down)
            self.style_button(self.double_button)
            self.double_button.pack(side=tk.LEFT, padx=10)
        
        self.time_remaining = 15
        self.timer_label = tk.Label(self.root, text=f"Time Remaining: {self.time_remaining} seconds ⏳", bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.timer_label.pack(pady=5)
        self.start_timer()

    def draw_hole_card(self, canvas, x, y):
        """Draw a face-down card (hole card)"""
        # Card rectangle
        canvas.create_rectangle(x-40, y-60, x+40, y+60, fill="#9933cc", outline="purple", width=3)
        # Card back pattern with theme emoji
        deco = self.get_theme_emoji()
        canvas.create_text(x, y, text=deco, font=("Comic Sans MS", 40, "bold"), fill="white")
        canvas.create_text(x, y-20, text=deco, font=("Comic Sans MS", 20), fill="white")
        canvas.create_text(x, y+20, text=deco, font=("Comic Sans MS", 20), fill="white")

    def ai_play_turn(self):
        player = self.players[self.current_player_idx]
        dealer_upcard = self.dealer.hand[0]
        if player.decide_hit(player.hand, dealer_upcard):
            player.hand.append(self.deck.deal_card())
            if self.calculate_hand_value(player.hand) > 21:
                self.next_player()
            else:
                self.play_player_turn()
        else:
            self.next_player()

    def start_timer(self):
        self.timer_label.config(text=f"Time Remaining: {self.time_remaining} seconds ⏳")
        if self.time_remaining <= 0:
            messagebox.showinfo("Timeout!", "Time's up! Auto-stand applied.")
            self.stand()
            return
        self.time_remaining -= 1
        self.timer_id = self.root.after(1000, self.start_timer)

    def cancel_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def hit(self):
        self.cancel_timer()
        player = self.players[self.current_player_idx]
        player.hand.append(self.deck.deal_card())
        self.play_player_turn()  # Always update UI to show the new card
        if self.calculate_hand_value(player.hand) > 21:
            # Show bust message after a short delay so the card is visible
            self.root.after(1000, lambda: (messagebox.showinfo("Bust!", f"{player.name} busted!"), self.next_player()))

    def double_down(self):
        self.cancel_timer()
        player = self.players[self.current_player_idx]
        if player.double_down():
            # Double down: double bet, get exactly one card, then stand
            player.hand.append(self.deck.deal_card())
            self.play_player_turn()  # Update UI to show the new card
            if self.calculate_hand_value(player.hand) > 21:
                # Show bust message after delay
                self.root.after(1000, lambda: (messagebox.showinfo("Bust!", f"{player.name} doubled down and busted!"), self.next_player()))
            else:
                # Automatically stand after double down
                self.root.after(1000, self.next_player)
        else:
            messagebox.showerror("Error", "Insufficient chips to double down!")

    def stand(self):
        self.cancel_timer()
        self.next_player()

    def next_player(self):
        self.current_player_idx += 1
        if self.current_player_idx >= len(self.players):
            self.dealer_turn()
        else:
            self.play_player_turn()

    def dealer_turn(self):
        while self.dealer.should_hit():
            self.dealer.hand.append(self.deck.deal_card())
        dealer_value = self.dealer.get_hand_value()
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Dealer's Final Hand 🎀", font=("Comic Sans MS", 20, "bold"), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        canvas = tk.Canvas(self.root, bg="#ffe6f0", width=900, height=300, highlightthickness=0)
        canvas.pack()
        for idx, card in enumerate(self.dealer.hand):
            x = 150 + idx * 150
            self.draw_card_box(canvas, card, x, 150)
        result_text = f"Dealer's Value: {dealer_value}\n"
        self.badge_achievements_this_round = []
        
        # Check if dealer has blackjack for insurance payouts
        dealer_has_blackjack = len(self.dealer.hand) == 2 and dealer_value == 21
        
        for player in self.players:
            player_value = self.calculate_hand_value(player.hand)
            win = False
            blackjack = False
            round_21 = False
            all_face = False
            all_red = False
            comeback = False
            streak = getattr(player, 'win_streak', 0)
            
            # Handle insurance payouts first
            if hasattr(player, 'insurance_bet') and player.insurance_bet > 0:
                if dealer_has_blackjack:
                    # Insurance pays 2:1
                    insurance_payout = player.insurance_bet * 3  # 2:1 plus original bet back
                    player.chips += insurance_payout
                    result_text += f"{player.name}: Insurance pays! +{insurance_payout - player.insurance_bet} chips\n"
                else:
                    result_text += f"{player.name}: Insurance loses.\n"
                player.insurance_bet = 0  # Reset insurance bet
            
            # Check for blackjack (21 with exactly 2 cards)
            is_player_blackjack = len(player.hand) == 2 and player_value == 21
            
            # Check win conditions
            if player_value > 21:
                result_text += f"{player.name} busted. Lost bet.\n"
                player.win_streak = 0
            elif dealer_value > 21 or player_value > dealer_value:
                # Player wins
                player.win_bet(is_blackjack=is_player_blackjack)
                player.wins += 1
                win = True
                # Streak logic
                player.win_streak = getattr(player, 'win_streak', 0) + 1
                
                # Set flags for achievements
                if is_player_blackjack:
                    blackjack = True
                    result_text += f"{player.name} wins with Blackjack! Pays 3:2! 🎉\n"
                else:
                    result_text += f"{player.name} wins! 🎉\n"
                
                # 21 exactly
                if player_value == 21:
                    round_21 = True
                # All face cards
                all_face = all(card.rank in ['J', 'Q', 'K'] for card in player.hand)
                # All red
                all_red = all(card.suit in ['Hearts', 'Diamonds'] for card in player.hand)
                # Comeback: won and chips were less than dealer before round
                if hasattr(self, 'dealer') and player.chips < self.dealer.chips:
                    comeback = True
                # Check and award badges
                new_badges, new_achievements = self.check_and_award_badges(
                    player, player.hand, win, blackjack, round_21, all_face, all_red, comeback, player.win_streak)
                if new_badges or new_achievements:
                    self.badge_achievements_this_round.append((player.name, new_badges, new_achievements))
            elif player_value == dealer_value:
                player.push_bet()
                result_text += f"{player.name} pushes. Bet returned.\n"
                player.win_streak = 0
            else:
                result_text += f"{player.name} loses.\n"
                player.win_streak = 0
            self.update_player_stats(player)
        self.last_round_results = result_text
        self.dealer_final_hand = list(self.dealer.hand)  # Save dealer's hand for next page
        self.result_label = tk.Label(self.root, text=result_text, bg="#ffe6f0", font=("Comic Sans MS", 12), fg="#9933cc")
        self.result_label.pack(pady=10)
        self.check_game_over()

    def check_game_over(self):
        losers = [player for player in self.players if player.chips <= 0]
        if len(losers) == len(self.players):
            self.coin_flip_tiebreaker()
            return
        elif losers:
            winner = max(self.players, key=lambda p: p.chips)
            self.clear_screen()
            result_text = f"{winner.name} wins! {winner.name} is crowned the Princess of the Palace 👑💖✨"
            self.result_label = tk.Label(self.root, text=result_text, font=("Comic Sans MS", 16), bg="#ffe6f0", fg="#9933cc")
            self.result_label.pack(pady=20)
            self.restart_button = tk.Button(self.root, text="Restart Game", command=self.setup_start_screen)
            self.style_button(self.restart_button)
            self.restart_button.pack(pady=20)
        else:
            self.show_leaderboard_menu()

    def coin_flip_tiebreaker(self):
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Both players ran out of chips! 👑", font=("Comic Sans MS", 16), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        self.flip_button = tk.Button(self.root, text="Flip Coin", command=self.flip_coin)
        self.style_button(self.flip_button)
        self.flip_button.pack(pady=20)

    def flip_coin(self):
        self.clear_screen()
        result = random.choice(['Heads', 'Tails'])
        winner = self.players[0] if result == 'Heads' else self.players[1]
        self.canvas = tk.Canvas(self.root, bg="#ffe6f0", width=600, height=400, highlightthickness=0)
        self.canvas.pack(pady=20)
        self.canvas.create_text(300, 50, text=f"Coin landed: {result}!", font=("Comic Sans MS", 28, "bold"), fill="purple")
        # Pink coin
        self.canvas.create_oval(200, 150, 400, 350, fill="#ff69b4", outline="purple", width=4)
        self.canvas.create_text(300, 250, text=result[0], font=("Comic Sans MS", 80, "bold"), fill="purple")
        self.canvas.create_text(300, 380, text=f"Winner: {winner.name} is crowned the Princess of the Palace 👑💖", font=("Comic Sans MS", 20, "bold"), fill="purple")
        self.restart_button = tk.Button(self.root, text="Return to Game", command=self.setup_start_screen)
        self.style_button(self.restart_button)
        self.restart_button.pack(pady=20)

    def show_leaderboard(self):
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Leaderboard ✨", font=("Comic Sans MS", 16), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        sorted_players = sorted(self.players, key=lambda p: p.chips, reverse=True)
        for player in sorted_players:
            label = tk.Label(self.root, text=f"{player.name}: {player.chips} chips", bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12))
            label.pack()
        # Back button returns to the previous round/leaderboard page, not next round
        self.back_button = tk.Button(self.root, text="Back", command=self.show_leaderboard_menu)
        self.style_button(self.back_button)
        self.back_button.pack(pady=10)

    def show_leaderboard_menu(self):
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Round Complete! ✨", font=("Comic Sans MS", 16), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        # Show dealer's final hand graphically and value (only once)
        if hasattr(self, 'dealer') and hasattr(self, 'dealer_final_hand'):
            dealer_hand_label = tk.Label(self.root, text="Dealer's Hand:", bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12, "bold"))
            dealer_hand_label.pack(pady=(5, 0))
            canvas = tk.Canvas(self.root, bg="#ffe6f0", width=900, height=180, highlightthickness=0)
            canvas.pack()
            for idx, card in enumerate(self.dealer_final_hand):
                x = 150 + idx * 150
                self.draw_card_box(canvas, card, x, 90)
            dealer_value = self.calculate_hand_value(self.dealer_final_hand)
            dealer_label = tk.Label(self.root, text=f"Dealer's Value: {dealer_value}", bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12, "bold"))
            dealer_label.pack(pady=2)
        # Show round results as a single label (old style), but remove duplicate dealer value
        if hasattr(self, 'last_round_results') and self.last_round_results:
            # Remove the first line if it starts with "Dealer's Value:" (to avoid duplicate)
            lines = self.last_round_results.split('\n')
            if lines and lines[0].startswith("Dealer's Value:"):
                lines = lines[1:]
            result_label = tk.Label(self.root, text='\n'.join(lines), bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12, "bold"))
            result_label.pack(pady=2)
        # Show badge/achievement notifications for this round
        if hasattr(self, 'badge_achievements_this_round') and self.badge_achievements_this_round:
            for name, badges, achievements in self.badge_achievements_this_round:
                if badges or achievements:
                    badge_str = ' '.join(badges)
                    ach_str = '\n'.join(achievements)
                    notif = tk.Label(self.root, text=f"{name} earned: {badge_str}\n{ach_str}", bg="#ffe6f0", fg="#e75480", font=("Comic Sans MS", 12, "bold"))
                    notif.pack(pady=2)
        self.leaderboard_button = tk.Button(self.root, text="Show Leaderboard", command=self.show_leaderboard)
        self.style_button(self.leaderboard_button)
        self.leaderboard_button.pack(pady=5)
        self.new_round_button = tk.Button(self.root, text="Play Next Round", command=self.restart_game)
        self.style_button(self.new_round_button)
        self.new_round_button.pack(pady=5)
        # Change Quit Game button to go to home page
        self.quit_button = tk.Button(self.root, text="Quit Game", command=self.setup_start_screen)
        self.style_button(self.quit_button)
        self.quit_button.pack(pady=5)

    def restart_game(self):
        self.current_player_idx = 0
        self.play_round()

    def calculate_hand_value(self, hand):
        value = sum(card.value for card in hand)
        aces = sum(1 for card in hand if card.rank == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    def load_player_stats(self):
        try:
            with open(self.leaderboard_file, "r") as f:
                data = json.load(f)
            # Migrate old format if needed
            for k, v in list(data.items()):
                if isinstance(v, int):
                    data[k] = {"wins": max(0, v), "badges": [], "achievements": []}
            return data
        except Exception:
            return {}

    def save_player_stats(self):
        with open(self.leaderboard_file, "w") as f:
            json.dump(self.player_stats, f, indent=2)

    def get_or_create_player(self, name):
        if name not in self.player_stats:
            self.player_stats[name] = {"wins": 0, "badges": [], "achievements": []}
        stats = self.player_stats[name]
        return Player(name, wins=stats["wins"], badges=stats["badges"], achievements=stats["achievements"])

    def update_player_stats(self, player):
        self.player_stats[player.name] = {
            "wins": player.wins,
            "badges": player.badges,
            "achievements": player.achievements
        }
        self.save_player_stats()

    # Badge rules
    def check_and_award_badges(self, player, hand, win, blackjack, round_21, all_face, all_red, comeback, streak):
        # If AI, skip
        if hasattr(player, 'is_ai') and player.is_ai:
            return [], []
        new_badges = []
        new_achievements = []
        # 🍧 Ice Cream: Get exactly 21 in a round
        if round_21 and "🍧" not in player.badges:
            player.badges.append("🍧")
            new_badges.append("🍧")
            new_achievements.append(f"{player.name} earned the Ice Cream🍧 for getting 21 exactly!")
        # 🪷 Pink Lotus: Reach 5 wins
        if player.wins >= 5 and "🪷" not in player.badges:
            player.badges.append("🪷")
            new_badges.append("🪷")
            new_achievements.append(f"{player.name} earned the Pink Lotus🪷 for getting five wins!")
        # 🦩 Flamingo: Win 3 rounds in a row
        if streak >= 3 and "🦩" not in player.badges:
            player.badges.append("🦩")
            new_badges.append("🦩")
            new_achievements.append(f"{player.name} earned the Flamingo🦩 for winning 3 rounds in a row!")
        # 🩰 Ballet Slipper: Win with only face cards
        if all_face and "🩰" not in player.badges:
            player.badges.append("🩰")
            new_badges.append("🩰")
            new_achievements.append(f"{player.name} earned the Ballet Slipper🩰 for winning with only face cards!")
        # 🌸 Cherry Blossom: Win with all hearts or diamonds
        if all_red and "🌸" not in player.badges:
            player.badges.append("🌸")
            new_badges.append("🌸")
            new_achievements.append(f"{player.name} earned the Cherry Blossom🌸 for winning with all hearts or diamonds!")
        # 💖 Heart Gem: Win with blackjack
        if blackjack and "💖" not in player.badges:
            player.badges.append("💖")
            new_badges.append("💖")
            new_achievements.append(f"{player.name} earned the Heart Gem💖 for winning with a blackjack!")
        # 🦄 Unicorn: Win after being behind in chips
        if comeback and "🦄" not in player.badges:
            player.badges.append("🦄")
            new_badges.append("🦄")
            new_achievements.append(f"{player.name} earned the Unicorn🦄 for winning after being behind in chips!")
        # 🎀 Bow Master: Earn all other badges
        all_badges = {"🍧", "🪷", "🦩", "🩰", "🌸", "💖", "🦄"}
        if all(b in player.badges for b in all_badges) and "🎀" not in player.badges:
            player.badges.append("🎀")
            new_badges.append("🎀")
            new_achievements.append(f"{player.name} earned the Bow Master🎀 for earning all other badges!")
        # AI Mode exclusive badges
        if hasattr(self, 'vs_ai_mode') and self.vs_ai_mode:
            # 🧸 Beat the AI 3 times
            if player.wins >= 3 and "🧸" not in player.badges:
                player.badges.append("🧸")
                new_badges.append("🧸")
                new_achievements.append(f"{player.name} earned the Teddy Bear🧸 for beating the AI 3 times!")
            # 🦋 Blackjack vs AI
            if blackjack and "🦋" not in player.badges:
                player.badges.append("🦋")
                new_badges.append("🦋")
                new_achievements.append(f"{player.name} earned the Butterfly🦋 for getting a blackjack against the AI!")
        for ach in new_achievements:
            if ach not in player.achievements:
                player.achievements.append(ach)
        return new_badges, new_achievements

    def show_achievements_leaderboard(self):
        self.clear_screen()
        self.title = tk.Label(self.root, text="🎀 Achievements + Leaderboard ✨", font=("Comic Sans MS", 18, "bold"), bg="#ffe6f0", fg="#9933cc")
        self.title.pack(pady=10)
        # Rankings by wins
        sorted_by_wins = sorted(self.player_stats.items(), key=lambda x: x[1]["wins"], reverse=True)
        win_frame = tk.LabelFrame(self.root, text="By Wins", font=("Comic Sans MS", 14, "bold"), bg="#ffe6f0", fg="#9933cc", bd=2, relief="groove", labelanchor="n")
        win_frame.pack(pady=10, padx=20, fill="x")
        for i, (name, stats) in enumerate(sorted_by_wins, 1):
            badges = ' '.join(stats["badges"])
            label = tk.Label(win_frame, text=f"{i}. {name} - {stats['wins']} wins  {badges}", bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12))
            label.pack(anchor="w", padx=10)
        # Rankings by badge count
        sorted_by_badges = sorted(self.player_stats.items(), key=lambda x: len(x[1]["badges"]), reverse=True)
        badge_frame = tk.LabelFrame(self.root, text="By Badges", font=("Comic Sans MS", 14, "bold"), bg="#ffe6f0", fg="#9933cc", bd=2, relief="groove", labelanchor="n")
        badge_frame.pack(pady=10, padx=20, fill="x")
        for i, (name, stats) in enumerate(sorted_by_badges, 1):
            badges = ' '.join(stats["badges"])
            label = tk.Label(badge_frame, text=f"{i}. {name} - {len(stats['badges'])} badges  {badges}", bg="#ffe6f0", fg="#9933cc", font=("Comic Sans MS", 12))
            label.pack(anchor="w", padx=10)
        # Back button
        self.back_button = tk.Button(self.root, text="Back", command=self.setup_start_screen)
        self.style_button(self.back_button)
        self.back_button.pack(pady=20)

    class AIPlayer(Player):
        def __init__(self, game):
            super().__init__("AI", chips=100)
            self.is_ai = True
            self.game = game
        def place_bet(self, amount=None):
            # AI bets a random amount between 10 and its chips, or all if less than 10
            if self.chips < 10:
                bet = self.chips
            else:
                bet = random.randint(10, min(50, self.chips))
            self.bet = bet
            self.chips -= bet
            return True
        def decide_hit(self, hand, dealer_upcard):
            # Simple AI: hit if value < 16, else stand
            # Use the game's calculate_hand_value method for consistent Ace handling
            value = self.game.calculate_hand_value(hand)
            return value < 16


if __name__ == '__main__':
    root = tk.Tk()
    game = BlackjackGame(root)
    root.mainloop()
