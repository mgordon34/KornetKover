from typing import List

from kornetkover.analysis.models.bet import Bet

class Tracker(object):
    def __init__(self):
        self.bets: List[Bet] = []

    def print_totals(self, bet_size: int = 100, stat: str = None):
        win_count = 0
        loss_count = 0
        total = 0
        for bet in self.bets:
            if stat and stat != bet.line.stat:
                continue

            odds = bet.line.over_odds if bet.side == "over" else bet.line.under_odds
            if bet.result == "win":
                win_count += 1
                total += self.calculate_return(odds, bet_size)
            else:
                loss_count += 1
                total -= bet_size
            

        display_str = stat if stat else "Total"
        winrate = win_count / (win_count + loss_count) if (win_count + loss_count) else 0
        print(f"======={display_str}========")
        print(f"WINS: {win_count}, LOSSES: {loss_count}, WIN RATE: {winrate}")
        print(f"Estimated Profit: ${total:,.2f}")

    def analyze_totals(self, stat: str = None):
        print(f"Totals for {stat}")
        max_diff = 0
        for bet in self.bets:
            if stat and stat != bet.line.stat:
                continue

            max_diff = max(max_diff, int(abs(bet.line.predicted_delta)))

        for i in range(0, (max_diff+1)*2):
            win_totals = 0
            win_count = 0
            loss_totals = 0
            loss_count = 0
            for bet in self.bets:
                if stat and stat != bet.line.stat:
                    continue

                if abs(bet.line.predicted_delta) < i/2.0 or abs(bet.line.predicted_delta) > (i/2.0)+.5:
                    continue

                if bet.result == "win":
                    win_totals += abs(bet.line.predicted_delta)
                    win_count += 1
                else:
                    loss_totals += abs(bet.line.predicted_delta)
                    loss_count += 1

            print(f"[{i/2}={i/2+.5}]wins {win_count}, losses {loss_count}")

        for i in range(0, (max_diff+1)*2):
            win_totals = 0
            win_count = 0
            loss_totals = 0
            loss_count = 0
            total = 0
            for bet in self.bets:
                if stat and stat != bet.line.stat:
                    continue
                
                if abs(bet.line.predicted_delta) < i/2.0:
                    continue

                if bet.result == "win":
                    win_totals += abs(bet.line.predicted_delta)
                    win_count += 1
                    odds = bet.line.over_odds if bet.side == "over" else bet.line.under_odds
                    total += self.calculate_return(odds, 100)
                else:
                    loss_totals += abs(bet.line.predicted_delta)
                    loss_count += 1
                    total -= 100


            print(f"[>{i/2.0}]wins {win_count}, losses {loss_count}, total: {total}")

    def print_long_shot_report(self, threshold: float = .25, stat: str = None) -> None:

        total_wins = 0
        total_losses = 0
        for bet in self.bets:
            if stat and stat != bet.line.stat:
                continue

            # if bet.line.predicted_delta < 0:
            #     continue

            if abs(bet.line.predicted_delta)/bet.line.line < threshold:# or bet.line.line <= 1.5:
                continue

            if bet.side == "over":
                if bet.actual > (bet.line.line):
                # if bet.actual > (bet.line.line + bet.line.line*.25):
                    # print(f"[{bet.date}]{bet.player.name} line: {bet.line.line} threshold: {bet.line.line + bet.line.line*.25} actual: {bet.actual}")
                    total_wins += 1
                else:
                    total_losses += 1
            else:
                if bet.actual < (bet.line.line):
                # if bet.actual < (bet.line.line - bet.line.line*.25):
                    # print(f"[{bet.date}]{bet.player.name} line: {bet.line.line} threshold: {bet.line.line - bet.line.line*.25} actual: {bet.actual}")
                    total_wins += 1
                else:
                    total_losses += 1


        winrate = total_wins / (total_wins + total_losses) if (total_wins + total_losses) else 0
        if winrate:
            print(f"{threshold} Long Shot {stat}: {total_wins}/{total_losses} winrate: {winrate}-------------------------------")

    def calculate_return(self, odds, bet_size):
        if odds < 0:
            return 100 / abs(odds) * bet_size
        else:
            return odds / 100 * bet_size

