from colorama import Fore, Style


def printe(msg):
    print(Fore.RED + '\u2717 ' + msg + Style.RESET_ALL)


def printg(msg):
    print(Fore.GREEN + '\u2713 ' + msg + Style.RESET_ALL)
