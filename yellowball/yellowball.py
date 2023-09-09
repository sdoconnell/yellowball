#!/usr/bin/env python3
"""yellowball

Version: 1.0
Author:  Sean O'Connell <sean@sdoconnell.net>
License: MIT
Homepage: https://github.com/sdoconnell/yellowball
About:
A Mega Millions lottery ticket checker and notifier

usage: yellowball.py [-h] [-f filename] [-c] [-l] [-w] [-m]
                  [--to address[,address...]] [--from address]
                  [--server IP or host] [-q] [-n num,num,...]
                  [-p number] [-x] [-d number] [-t YYYY-MM-DD]
                  [-v]

optional arguments:
  -h, --help            show this help message and exit
  -f filename, --file filename
                        ticket file name
  -c, --no-color        disable color output
  -l, --last-only       last draw only
  -w, --winners-only    show winners only
  -m, --send-mail       send results via email
  --to address[,address...]
                        mail recipient address(es)
  --from address        mail sender address
  --server IP or host   mail server
  -q, --quick-pick      generate quick pick
  -n num,num,..., --numbers num,num,...
                        white ball numbers (5)
  -p number, --megaball number
                        mega ball
  -x, --megaplier       megaplier option
  -d number, --draws number
                        number of draws
  -t YYYY-MM-DD, --purchased YYYY-MM-DD
                        ticket purchase date
  -v, --version         show version info

"""
import json
import configparser
import sys
import os.path
import argparse
import smtplib
import random
from datetime import datetime

import requests

APP_NAME = "yellowball"
APP_VERS = "1.0"


class Ticket():
    """Mega Millions lottery ticket operations.

    Attributes:
        no_color (bool):     disable color output.
        last_only (bool):    only show the last result.
        winners_only (bool): only show winning results.
        send_mail (bool):    send results by email.
        mail_to (str):       email recipient address.
        mail_from (str):     email sender address.
        mail_server (str):   SMTP server address.

    """
    def __init__(
            self,
            no_color=False,
            last_only=False,
            winners_only=False,
            send_mail=False,
            mail_to=None,
            mail_from=None,
            mail_server=None):
        """Initialize a Ticket() object."""
        self.no_color = no_color
        self.last_only = last_only
        self.winners_only = winners_only
        self.send_mail = send_mail
        self.mail_to = mail_to
        self.mail_from = mail_from
        self.mail_server = mail_server

        self.threshold = 999

        # define colors
        if self.no_color:
            self.red = ''
            self.yellow = ''
            self.enc = ''
            self.bold = ''
        else:
            self.red = '\033[31m'
            self.yellow = '\033[33m'
            self.enc = '\033[0m'
            self.bold = '\033[1m'

    @staticmethod
    def _calc_winnings(matched, megaball, megaplier):
        """Calculates lottery ticket winning ticket value.

        Args:
            matched (int):    the number of numbers matched.
            megaball (bool):  the megaball matched.
            megaplier (int):  the Megaplier multiplier.

        Returns:
            winnings (int):   the value of the winning ticket.

        """
        # rewards:
        # 5+mb = jackpot
        # 5 = $1,000,000 x megaplier
        # 4+mb = $10,000 x megaplier
        # 4 = $500 x megaplier
        # 3+mb = $200 x megaplier
        # 3 or 2+mb = $10 x megaplier
        # 1+mb = $4 x megaplier
        # 0+mb = $2 x megaplier
        if megaball:
            if matched == 4:
                winnings = 10000 * megaplier
            elif matched == 3:
                winnings = 200 * megaplier
            elif matched == 2:
                winnings = 10 * megaplier
            elif matched == 1:
                winnings = 4 * megaplier
            else:
                winnings = 2 * megaplier
        else:
            if matched == 5:
                winnings = 1000000 * megaplier
            elif matched == 4:
                winnings = 500 * megaplier
            elif matched == 3:
                winnings = 10 * megaplier
            else:
                winnings = 0
        return winnings

    @staticmethod
    def _format_ticket(ticketdata, remaining):
        """Prints ticket information.

        Args:
            ticketdata (dict): the ticket information.
            remaining (int):   remaining draws on the ticket.

        Returns:
            formatted (str): the formatted ticket output.

        """
        numbers = ticketdata.get('numbers')
        megaball = ticketdata.get('megaball')
        purchased = datetime.strftime(ticketdata.get('purchased'), "%Y-%m-%d")
        draws = ticketdata.get('draws')
        if ticketdata.get('megaplier'):
            megaplier = "Yes"
        else:
            megaplier = "No"
        numbers = ', '.join(f'{x:02d}' for x in numbers)
        formatted = (
            "\nTicket info\n"
            "===========\n"
            f"Purchased: {purchased}\n"
            f"Draws: {draws}\n"
            f"Remaining: {remaining}\n"
            f"Numbers: {numbers} [{megaball:02d}]\n"
            f"Megaplier: {megaplier}\n\n"
        )

        return formatted

    @staticmethod
    def _get_winners(ticketdate, draws):
        """Collects and parses the winning numbers, returning them in a dict.

        Args:
            ticketdate (obj):   the purchase date of the ticket.
            draws (int):        the number of draws on the ticket.

        Returns:
            winners (dict):     the winning numbers.

        """
        results = {}
        today = datetime.now()

        # API URL for lottery results
        apiurl = "https://data.ny.gov/resource/5xaw-6ayf.json"
        requrl = (
            f"{apiurl}?$where=draw_date between '"
            f'{datetime.strftime(ticketdate, "%Y-%m-%dT00:00:00.000")}'
            "' and '"
            f'{datetime.strftime(today, "%Y-%m-%dT00:00:00.000")}'
            "'"
        )

        try:
            response = requests.get(requrl)
        except requests.exceptions.RequestException:
            print("Error: could not retrieve results! "
                  "Check network connection.")
            sys.exit(1)
        else:
            data = json.loads(response.text)
            for item in data:
                drawdate = datetime.fromisoformat(item.get("draw_date"))
                numbers = item.get("winning_numbers")
                mmult = item.get("multiplier")
                mball = item.get("mega_ball")
                if (drawdate and
                        mmult and
                        numbers):
                    if drawdate >= ticketdate:
                        numbers = numbers.split(" ")
                        result = {
                            'ball1': int(numbers[0]),
                            'ball2': int(numbers[1]),
                            'ball3': int(numbers[2]),
                            'ball4': int(numbers[3]),
                            'ball5': int(numbers[4]),
                            'mball': int(mball),
                            'mmult': int(mmult)
                        }
                        results[drawdate] = result
            covered = list(sorted(results.keys()))[0:draws]
            winners = {}
            for draw in covered:
                winners[draw] = results[draw]

            return winners

    def check(
            self,
            ticketdata):
        """Checks ticket against winning numbers.

        Args:
            ticketdata (dict): the lottery ticket data.

        """
        draws = ticketdata.get('draws')
        purchased = ticketdata.get('purchased')
        numbers = ticketdata.get('numbers')
        megaball = ticketdata.get('megaball')
        megaplier = ticketdata.get('megaplier')

        winners = self._get_winners(purchased, draws)
        remaining = draws - len(winners)
        output = self._format_ticket(ticketdata, remaining)
        totalvalue = 0
        hitjackpot = False
        output += "Results:\n"
        if self.last_only:
            if len(winners) > 1:
                keys = list(winners.keys())
                del keys[-1]
                for key in keys:
                    del winners[key]
        for drawdate in winners:
            ball1 = winners[drawdate].get('ball1')
            ball2 = winners[drawdate].get('ball2')
            ball3 = winners[drawdate].get('ball3')
            ball4 = winners[drawdate].get('ball4')
            ball5 = winners[drawdate].get('ball5')
            mball = winners[drawdate].get('mball')
            mmult = winners[drawdate].get('mmult')
            if (ball1 and
                    ball2 and
                    ball3 and
                    ball4 and
                    ball5 and
                    mball and
                    mmult):
                drawing = [ball1, ball2, ball3, ball4, ball5]
                matched = 0
                for number in numbers:
                    if number in drawing:
                        matched += 1
                if megaball == mball:
                    got_mb = True
                    mbstring = " + megaball"
                else:
                    got_mb = False
                    mbstring = ""
                if megaplier:
                    mmstring = f" (x{mmult} megaplier)"
                    got_mm = mmult
                else:
                    mmstring = ""
                    got_mm = 1

                ball1 = f"{ball1:02d}"
                ball2 = f"{ball2:02d}"
                ball3 = f"{ball3:02d}"
                ball4 = f"{ball4:02d}"
                ball5 = f"{ball5:02d}"
                mball = f"{self.yellow}{mball:02d}{self.enc}"

                drawing = (
                        f"{datetime.strftime(drawdate, '%Y-%m-%d')} ({ball1},{ball2},{ball3},"
                        f"{ball4},{ball5} [{mball}])"
                )

                if matched == 5 and got_mb:
                    result = (
                            f"{self.bold}{self.red}{drawdate} You won! "
                            f"[matched 5 numbers + megaball = "
                            f"JACKPOT!]{self.enc}"
                    )
                    hitjackpot = True
                elif matched < 3 and not got_mb:
                    if not self.winners_only:
                        result = "The ticket was not a winner."
                else:
                    amount = self._calc_winnings(matched, got_mb, got_mm)
                    amountstring = f"${amount}"
                    totalvalue += amount
                    if amount > self.threshold:
                        textcolor = self.red
                    else:
                        textcolor = self.yellow
                    result = (
                        f"{self.bold}{textcolor}You won! "
                        f"[matched {matched} numbers"
                        f"{mbstring}{mmstring} = "
                        f"{amountstring}]{self.enc}"
                    )
                output += f"{drawing} - {result}\n"
        if len(winners) == 0:
            output += "No results yet.\n"
        if hitjackpot is True and totalvalue > 0:
            tvstring = f"JACKPOT! (+${totalvalue})"
            textbold = self.bold
            textcolor = self.red
        elif hitjackpot is True:
            tvstring = "JACKPOT!"
            textbold = self.bold
            textcolor = self.red
        elif totalvalue > self.threshold:
            tvstring = f"${totalvalue}"
            textbold = self.bold
            textcolor = self.red
        elif totalvalue > 0:
            tvstring = f"${totalvalue}"
            textbold = self.bold
            textcolor = self.yellow
        else:
            tvstring = "$0"
            textbold = ""
            textcolor = ""
        output += (
                f"\n{textbold}{textcolor}Total ticket "
                f"value: {tvstring}{self.enc}\n"
        )
        if self.send_mail:
            subject = 'Mega Millions Results'
            # prepare the message
            message = (
                f"From: {self.mail_from}\n"
                f"To: {', '.join(self.mail_to)}\n"
                f"Subject: {subject}\n\n"
                f"{output}\n"
            )
            # send the mail
            server = smtplib.SMTP(self.mail_server)
            server.sendmail(self.mail_from, self.mail_to, message)
            server.quit()
        else:
            print(output)

    def parse_file(self, ticketfile):
        """Parses a lottery ticket file.

        Args:
            ticketfile (str):   the path of the lottery ticket file.

        Returns:
            ticketdata (dict):   the lottery ticket information.

        """
        config = configparser.ConfigParser()
        filename = os.path.expandvars(
                        os.path.expanduser(ticketfile))
        invalid = False
        if (os.path.exists(filename) and
                os.path.isfile(filename)):
            try:
                config.read(filename)
            except configparser.ParsingError:
                invalid = True
            else:
                if 'ticket' in config:
                    numbers = config.get('ticket', 'numbers')
                    if numbers:
                        numbers = str(numbers).replace(' ', '')
                    megaball = config.getint('ticket', 'megaball')
                    megaplier = config.getboolean('ticket', 'megaplier')
                    draws = config.getint('ticket', 'draws')
                    purchased = config.get('ticket', 'purchased')
                    ticketdata = self.validate(
                            numbers=numbers,
                            megaball=megaball,
                            megaplier=megaplier,
                            draws=draws,
                            purchased=purchased)
                    if not ticketdata:
                        invalid = True
                else:
                    invalid = True
            if invalid:
                print("ERROR: invalid ticket file.")
                sys.exit(1)
            else:
                return ticketdata
        else:
            print("ERROR: Ticket file not found.")
            sys.exit(1)

    @staticmethod
    def quick_pick():
        """Generates a Mega Millions quick pick tick."""
        rand_wb = sorted(random.sample(range(1, 70), 5))
        numbers = ", ".join(f"{x:02d}" for x in rand_wb)
        rand_mb = random.randrange(1, 26, 1)
        megaball = f"{rand_mb:02d}"
        print(
            "\nQuick pick:\n"
            "===========\n"
            f"Numbers:   {numbers}\n"
            f"Megaball: {megaball}\n\n"
        )

    @staticmethod
    def validate(
            numbers=None,
            megaball=None,
            draws=None,
            purchased=None,
            megaplier=False):
        """Validate input/ticket data and return a valid ticket or None.

        Args:
            numbers (str):    the white ball numbers.
            megaball (int):   the megaball number.
            draws (int):      the number of draws on the ticket.
            purchased (str):  the ticket purchase date.
            megaplier (bool): megaplier option.
        Returns:
            ticketdata (dict) or None:  the validated ticket data.

        """
        invalid = False

        # white ball numbers
        if numbers:
            numbers = numbers.split(',')
            valid_numbers = []
            for number in numbers:
                try:
                    if int(number) < 70:
                        valid_numbers.append(int(number))
                except TypeError:
                    invalid = True
            if len(valid_numbers) != 5:
                invalid = True
        else:
            invalid = True

        # megaball
        try:
            if int(megaball) < 26:
                megaball = int(megaball)
        except TypeError:
            invalid = True

        # draws
        try:
            if draws:
                draws = int(draws)
            else:
                draws = 1
        except TypeError:
            invalid = True

        # purchased
        try:
            testdate = datetime.fromisoformat(str(purchased))
        except ValueError:
            invalid = True
        else:
            purchased = testdate

        if not invalid:
            ticketdata = {
                "numbers": sorted(valid_numbers),
                "megaball": megaball,
                "draws": draws,
                "purchased": purchased,
                "megaplier": megaplier
            }
        else:
            ticketdata = None

        return ticketdata


def parse_args():
    """Parses and returns command arguments.

    Returns:
        args (dict):    the command arguments.
        parser (obj):   the configparser object.

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        metavar="filename",
        dest="ticketfile",
        help="ticket file name")
    parser.add_argument(
        "-c",
        "--no-color",
        help="disable color output",
        dest="no_color",
        action="store_true")
    parser.add_argument(
        "-l",
        "--last-only",
        help="last draw only",
        dest="last_only",
        action="store_true")
    parser.add_argument(
        "-w",
        "--winners-only",
        help="show winners only",
        dest="winners_only",
        action="store_true")
    parser.add_argument(
        "-m",
        "--send-mail",
        help="send results via email",
        dest="send_mail",
        action="store_true")
    parser.add_argument(
        "--to",
        metavar="address[,address...]",
        help="mail recipient address(es)",
        dest="mail_to")
    parser.add_argument(
        "--from",
        metavar="address",
        help="mail sender address",
        dest="mail_from")
    parser.add_argument(
        "--server",
        metavar="IP or host",
        help="mail server",
        dest="mail_server")
    parser.add_argument(
        "-q",
        "--quick-pick",
        help="generate quick pick",
        dest="quick_pick",
        action="store_true")
    parser.add_argument(
        "-n",
        "--numbers",
        metavar="num,num,...",
        dest="numbers",
        help="white ball numbers (5)")
    parser.add_argument(
        "-p",
        "--megaball",
        metavar="number",
        dest="megaball",
        help="megaball",
        type=int)
    parser.add_argument(
        "-x",
        "--megaplier",
        help="megaplier option",
        dest="megaplier",
        action="store_true")
    parser.add_argument(
        "-d",
        "--draws",
        metavar="number",
        dest="draws",
        help="number of draws",
        type=int)
    parser.add_argument(
        "-t",
        "--purchased",
        dest="purchased",
        metavar="YYYY-MM-DD",
        help="ticket purchase date")
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        action="store_true",
        help="show version info")
    args = parser.parse_args()

    return args, parser


def main():
    """Main loop."""
    args, parser = parse_args()

    if args.version:
        print(f"{APP_NAME} {APP_VERS}")
        sys.exit(0)

    # special handling for email option
    if args.send_mail and not (args.mail_to and args.mail_from):
        print(
            "ERROR: sending mail requires sender and "
            "recipient addresses (--to and --from).")
        sys.exit(1)
    else:
        mail = args.send_mail
    if args.mail_from:
        sender = str(args.mail_from)
    else:
        sender = None
    if args.mail_to:
        recipients = str(args.mail_to).split(",")
    else:
        recipients = None
    if not args.mail_server:
        server = "localhost"
    else:
        server = str(args.mail_server)
    if args.send_mail:
        args.no_color = True

    ticket = Ticket(
            no_color=args.no_color,
            last_only=args.last_only,
            winners_only=args.winners_only,
            send_mail=mail,
            mail_to=recipients,
            mail_from=sender,
            mail_server=server)

    if args.quick_pick:
        ticket.quick_pick()
    elif args.ticketfile:
        ticketdata = ticket.parse_file(args.ticketfile)
        ticket.check(ticketdata)
    else:
        if (args.numbers and
                args.megaball and
                args.purchased):
            ticketdata = ticket.validate(
                            numbers=args.numbers,
                            megaball=args.megaball,
                            draws=args.draws,
                            purchased=args.purchased,
                            megaplier=args.megaplier)
            if ticketdata:
                ticket.check(ticketdata)
            else:
                parser.print_help()
        else:
            parser.print_help()


# entry point
if __name__ == "__main__":
    main()
