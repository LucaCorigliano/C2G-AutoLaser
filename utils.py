class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    DEBUG = '\033[90m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    line = f"{OKCYAN}[ \u2022 ]{ENDC}"
    check = f"{OKGREEN}[ \u2713 ]{ENDC}"
    wait = f"{WARNING}[ \u2026 ]{ENDC}"
    userwait = f"{BOLD}[ \u2026 ]{ENDC}"
    cross = f"{FAIL}[ \u2717 ]{ENDC}"
    space = "     "
    laser = f"{OKGREEN}[ ⚡ ]{ENDC}"