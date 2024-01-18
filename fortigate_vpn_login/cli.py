# -*- coding: utf-8 -*-
"""
    fortigate_vpn_login.cli
    ~~~~~~~~~~~~~~~~~~~~~~

    This is the CLI interface for running the package.
"""
import logging
import os
import subprocess
import sys
import webbrowser
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import fortigate_vpn_login.webserver as webserver
from fortigate_vpn_login import __version__, __description__, logger
from fortigate_vpn_login import utils, config
from fortigate_vpn_login.fortigate import Fortigate


def main() -> int:
    """
    Main method which is called by CLI.

    Returns:
        int: The status from the program.

    Exit codes:
        0: Everything went well.
        1: General error while connecting to the VPN
        2: Usage/syntax error
    """
    # main program argument parser
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
        description=(
            f"fortigate-vpn-login {__version__}{os.linesep}"
            f"{__description__}"
        )
    )

    parser.add_argument(
        '-d',
        '--debug',
        help='Set LOG_LEVEL to DEBUG.',
        dest="DEBUG_MODE",
        action='store_true'
    )

    parser.add_argument(
        '-q',
        '--quiet',
        help='Do not log at all.',
        dest="QUIET_MODE",
        action='store_true'
    )

    parser.add_argument(
        '--configure',
        help='Interactive configuration.',
        dest='INTERACTIVE_CONFIGURE',
        action='store_true'
    )

    parser.add_argument(
        '-s',
        '--forti-url',
        help='URL of the Fortigate VPN server.',
        dest='FORTI_URL'
    )

    # parse the arguments, show in the screen if needed, etc
    parser = parser.parse_args()

    if parser.DEBUG_MODE:
        logger.setLevel("DEBUG")
        logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "DEBUG"))
        # TODO: on debug mode, change log format to
        # '[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)s: %(funcName)s()] %(message)s'))
    else:
        # defaults to info
        logger.setLevel("INFO")
        logging.getLogger().setLevel(os.getenv("LOG_LEVEL", "INFO"))

    if parser.QUIET_MODE:
        logging.disable(logging.CRITICAL)

    # load configuration
    options = config.Config()

    # do we need to configure interactively?
    if parser.INTERACTIVE_CONFIGURE:
        options.configure()
        options.write()
        return 0

    # server url
    if not parser.FORTI_URL:
        fortigate_vpn_url = options.get('forti_url')
        if not fortigate_vpn_url:
            print('ERROR: "forti_url" option is not set. Use "-s" or "--configure" to set it.')
            return 2
    else:
        fortigate_vpn_url = parser.FORTI_URL

    # establish connection to the Fortigate VPN Server, grab info, etc
    fortigate = Fortigate(fortigate_vpn_url)
    url = fortigate.connect_saml()
    if not url:
        return 1

    # webserver to get the response from the IDP through browser request
    ws = webserver.run()
    webbrowser.open(url)
    auth_id = webserver.return_token()
    webserver.quit(ws)

    if auth_id == '-1':
        print("ERROR: Invalid ID from provider. Try again or contact your provider support.")
        return 1

    cookie_svpn = fortigate.get_cookie(auth_id)

    print(cookie_svpn)

    return 0


if __name__ == "__main__":
    sys.exit(main())
