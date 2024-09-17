from enum import Enum
from colorama import Fore, Style, init
from datetime import datetime
from .utils import get_dict_ascii_tree


class QueryStatus(Enum):
    """Query Status Enumeration.

    Describes status of query about a given task.
    """

    STARTED = 'Started'
    STOPPED = 'Stopped'
    ACTIVE = 'Active'
    FAILED = 'Failed'
    STALE = 'Stale'

    def __str__(self):
        """Convert Object To String.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        Nicely formatted string to get information about this object.
        """
        return self.value


class QueryNotify:
    """Query Notify Object.

    Base class that describes methods available to notify the results of
    a query.
    It is intended that other classes inherit from this base class and
    override the methods to implement specific functionality.
    """

    def __init__(self, result=None):
        """Create Query Notify Object.

        Contains information about a specific method of notifying the results
        of a query.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """

        self.result = result

        return

    def start(self, message=None, id_type="task"):
        """Notify Start.

        Notify method for start of query.  This method will be called before
        any queries are performed.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        message                -- Object that is used to give context to start
                                  of query.
                                  Default is None.

        Return Value:
        Nothing.
        """

        return

    def update(self, result):
        """Notify Update.

        Notify method for query result.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.

        Return Value:
        Nothing.
        """

        self.result = result

        return

    def finish(self, message=None):
        """Notify Finish.

        Notify method for finish of query.  This method will be called after
        all queries have been performed.  This method will typically be
        overridden by higher level classes that will inherit from it.

        Keyword Arguments:
        self                   -- This object.
        message                -- Object that is used to give context to start
                                  of query.
                                  Default is None.

        Return Value:
        Nothing.
        """

        return

    def __str__(self):
        """Convert Object To String.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        Nicely formatted string to get information about this object.
        """
        result = str(self.result)

        return result


class QueryNotifyPrint(QueryNotify):
    """Query Notify Print Object.

    Query notify class that prints results.
    """

    def __init__(
        self,
        result=None,
        verbose=False,
        color=True,
    ):
        """Create Query Notify Print Object.

        Contains information about a specific method of notifying the results
        of a query.

        Keyword Arguments:
        self                   -- This object.
        result                 -- Object of type QueryResult() containing
                                  results for this query.
        verbose                -- Boolean indicating whether to give verbose output.
        color                  -- Boolean indicating whether to color terminal output

        Return Value:
        Nothing.
        """

        # Colorama module's initialization.
        init(autoreset=True)

        super().__init__(result)
        self.verbose = verbose
        self.color = color

        return

    def make_colored_terminal_notify(
        self, status, text, status_color, text_color, appendix
    ):
        text = [
            f"{Style.BRIGHT}{Fore.WHITE}[{status_color}{status}{Fore.WHITE}]"
            + f"{text_color} {text}: {Style.RESET_ALL}"
            + f"{appendix}"
        ]
        return "".join(text)

    def make_simple_terminal_notify(
        self, status, text, status_color, text_color, appendix
    ):
        return f"[{status}] {text}: {appendix}"

    def make_terminal_notify(self, *args):
        if self.color:
            return self.make_colored_terminal_notify(*args)
        else:
            return self.make_simple_terminal_notify(*args)

    def start(self, message, id_type):
        """Notify Start.

        Will print the title to the standard output.

        Keyword Arguments:
        self                   -- This object.
        message                -- String containing username that the series
                                  of queries are about.

        Return Value:
        Nothing.
        """

        title = f"Checking {id_type}"
        if self.color:
            print(
                Style.BRIGHT
                + Fore.GREEN
                + "["
                + Fore.YELLOW
                + "*"
                + Fore.GREEN
                + f"] {title}"
                + Fore.WHITE
                + f" {message}"
                + Fore.GREEN
                + " on:"
            )
        else:
            print(f"[*] {title} {message} on:")

    def _colored_print(self, fore_color, msg):
        if self.color:
            print(Style.BRIGHT + fore_color + msg)
        else:
            print(msg)

    def _send_message(self, message, color, items, title, symbol):
        now = datetime.now().isoformat(' ', 'seconds')
        msg = f"[{symbol}][{title}][{now}] {message}"
        if len(items) > 0:
            msg += get_dict_ascii_tree(items)
        self._colored_print(color, msg)

    def error(self, message: str, items=[], title='', symbol="!"):
        self._send_message(message, Fore.RED, items, title, symbol)

    def warning(self, message: str, items=[], title='', symbol="-"):
        self._send_message(message, Fore.YELLOW, items, title, symbol)

    def info(self, message: str, items=[], title='', symbol="*"):
        self._send_message(message, Fore.BLUE, items, title, symbol)

    def __str__(self):
        """Convert Object To String.

        Keyword Arguments:
        self                   -- This object.

        Return Value:
        Nicely formatted string to get information about this object.
        """
        result = str(self.result)

        return result


notify = QueryNotifyPrint()
