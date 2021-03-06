"""
Commands

Commands describe the input the player can do to the game.

"""

from evennia import Command as BaseCommand
from evennia import default_cmds
from evennia import settings
from evennia.comms.models import Msg


class Command(BaseCommand):
    """
    Inherit from this if you want to create your own
    command styles. Note that Evennia's default commands
    use MuxCommand instead (next in this module).

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order:
        - at_pre_command(): If this returns True, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_command(): Extra actions, often things done after
            every command, like prompts.

    """
    # these need to be specified

    key = "MyCommand"
    aliases = []
    locks = "cmd:all()"
    help_category = "General"

    # optional
    # auto_help = False      # uncomment to deactive auto-help for this command.
    # arg_regex = r"\s.*?|$" # optional regex detailing how the part after
                             # the cmdname must look to match this command.

    # (we don't implement hook method access() here, you don't need to
    #  modify that unless you want to change how the lock system works
    #  (in that case see evennia.commands.command.Command))

    def at_pre_cmd(self):
        """
        This hook is called before `self.parse()` on all commands.
        """
        pass

    def parse(self):
        """
        This method is called by the `cmdhandler` once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from `self.func()` (see below).

        The following variables are available to us:
           # class variables:

           self.key - the name of this command ('mycommand')
           self.aliases - the aliases of this cmd ('mycmd','myc')
           self.locks - lock string for this command ("cmd:all()")
           self.help_category - overall category of command ("General")

           # added at run-time by `cmdhandler`:

           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following `self.cmdstring`.
           self.cmdset - the `cmdset` from which this command was picked. Not
                         often used (useful for commands like `help` or to
                         list all available commands etc).
           self.obj - the object on which this command was defined. It is often
                         the same as `self.caller`.
        """
        pass

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        self.caller.msg("Command called!")

    def at_post_cmd(self):
        """
        This hook is called after `self.func()`.
        """
        pass


class MuxCommand(default_cmds.MuxCommand):
    """
    This sets up the basis for Evennia's 'MUX-like' command style.
    The idea is that most other Mux-related commands should
    just inherit from this and don't have to implement parsing of
    their own unless they do something particularly advanced.

    A MUXCommand command understands the following possible syntax:

        name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]

    The `name[ with several words]` part is already dealt with by the
    `cmdhandler` at this point, and stored in `self.cmdname`. The rest is stored
    in `self.args`.

    The MuxCommand parser breaks `self.args` into its constituents and stores them
    in the following variables:
        self.switches = optional list of /switches (without the /).
        self.raw = This is the raw argument input, including switches.
        self.args = This is re-defined to be everything *except* the switches.
        self.lhs = Everything to the left of `=` (lhs:'left-hand side'). If
                     no `=` is found, this is identical to `self.args`.
        self.rhs: Everything to the right of `=` (rhs:'right-hand side').
                    If no `=` is found, this is `None`.
        self.lhslist - `self.lhs` split into a list by comma.
        self.rhslist - list of `self.rhs` split into a list by comma.
        self.arglist = list of space-separated args (including `=` if it exists).

    All args and list members are stripped of excess whitespace around the
    strings, but case is preserved.
    """

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        # this can be removed in your child class, it's just
        # printing the ingoing variables as a demo.
        super(MuxCommand, self).func()


def append_help(original_help, new_help):
    """
    Helper for attaching additional help documentation to Evennia built-ins.
    """
    divider = '-' * settings.CLIENT_DEFAULT_WIDTH
    return original_help + "\n" + divider + "\n" + new_help


class CmdPage(default_cmds.CmdPage):
    """
    Alternative Usage:
      p is an alias for page
      p[age] <message>
          to page the last people you paged who were online
      p[age] [<player> <player>... = <message>]
          supports space delimited player lists
    """
    __doc__ = append_help(default_cmds.CmdPage.__doc__, __doc__)
    aliases = ['tell', 'p']

    def parse(self):
        caller = self.caller

        raw = self.args
        args = raw.strip()
        lhs = rhs = []
        lhs2 = rhs2 = []
        recv = None

        # get the messages we've sent (not to channels)
        pages_we_sent = Msg.objects.get_messages_by_sender(caller,
                                                 exclude_channel_messages=True)
        if args:
            # split out args that are addressed and those that aren't
            if '=' in args:
                lhs, rhs = [arg.strip() for arg in args.split('=', 1)]
                print(type(lhs))
                # support space delimited receiver list
                if len(lhs.split(' ')) > 1:
                    lhs = ','.join(lhs.split(' '))
                    self.args = lhs + '=' + rhs
            elif pages_we_sent:
                temp_thing = None
                # `page <int>` is parsed later for recall history feature
                try:
                    temp_thing = int(args)
                except ValueError:
                    # split out switches
                    if args.startswith('/'):
                        lhs2, rhs2 = [arg.strip() for arg in args.split(' ', 1)]
                    else:
                        rhs2 = [arg.strip() for arg in args]
                    # get the last receivers of messages sent by caller
                    # sans bits that were offline at the time
                    recv = ",".join(obj.key for obj in pages_we_sent[-1].receivers)
                    args = ''.join(lhs2) + ' ' + recv + '=' + ''.join(rhs2)
                    self.args = args.strip()
                    pass
        super(CmdPage, self).parse()


class CmdIC(default_cmds.CmdIC):
    """
    Alternative Usage:
      @ic/home [<character>]
          override default @ic behavior to go directly to the character's @home
      @ic/hub [<character>]
          override default @ic behavior to go directly to the Spaceport Hub
    """
    __doc__ = append_help(default_cmds.CmdPage.__doc__, __doc__)
    def parse(self):
        session = self.session

        # Take advantage of parsing.
        super(CmdIC, self).parse()

        if 'hub' not in self.switches and 'home' not in self.switches:
            session.dest = 'last'
        elif 'hub' in self.switches:
            session.dest = 'hub'
        else:
            session.dest = 'home'
