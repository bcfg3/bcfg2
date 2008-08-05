'''Bcfg2 logging support'''
__revision__ = '$Revision$'

import copy, fcntl, logging, logging.handlers, math, socket, struct, sys, termios, types

logging.raiseExceptions=0

def print_attributes(attrib):
    ''' Add the attributes for an element'''
    return ' '.join(['%s="%s"' % data for data in attrib.iteritems()])

def print_text(text):
    ''' Add text to the output (which will need normalising '''
    charmap = {'<':'&lt;', '>':'&gt;', '&':'&amp;'}
    return ''.join([charmap.get(char, char) for char in text]) + '\n'
        
def xml_print(element, running_indent=0, indent=4):
    ''' Add an element and its children to the return string '''
    if (len(element.getchildren()) == 0) and (not element.text):
        ret = (' ' * running_indent)
        ret += '<%s %s/>\n' % (element.tag, print_attributes(element.attrib))
    else:
        child_indent = running_indent + indent
        ret = (' ' * running_indent)
        ret += '<%s%s>\n' % (element.tag, print_attributes(element))
        if element.text:                
            ret += (' '* child_indent) + print_text(element.text)
        for child in element.getchildren():
            ret += xml_print(child, child_indent, indent)
            ret += (' ' * running_indent) +  '</%s>\n' % (element.tag)
        if element.tail:
            ret += (' ' * child_indent) + print_text(element.tail)
    return ret

class TermiosFormatter(logging.Formatter):
    '''The termios formatter displays output in a terminal-sensitive fashion'''

    def __init__(self, fmt=None, datefmt=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        if sys.stdout.isatty():
            # now get termios info
            try:
                self.width = struct.unpack('hhhh', fcntl.ioctl(0, termios.TIOCGWINSZ,
                                                               "\000"*8))[1]
                if self.width == 0:
                    self.width = 80
            except:
                self.width = 80
        else:
            # output to a pipe
            self.width = 32768

    def format(self, record):
        '''format a record for display'''
        returns = []
        line_len = self.width
        if type(record.msg) in types.StringTypes:
            for line in record.msg.split('\n'):
                if len(line) <= line_len:
                    returns.append(line)
                else:
                    inner_lines = int(math.floor(float(len(line)) / line_len))+1
                    for i in xrange(inner_lines):
                        returns.append("%s" % (line[i*line_len:(i+1)*line_len]))
        elif type(record.msg) == types.ListType:
            if not record.msg:
                return ''
            record.msg.sort()
            msgwidth = self.width
            columnWidth = max([len(item) for item in record.msg])
            columns = int(math.floor(float(msgwidth) / (columnWidth+2)))
            lines = int(math.ceil(float(len(record.msg)) / columns))
            for lineNumber in xrange(lines):
                indices = [idx for idx in [(colNum * lines) + lineNumber
                                           for colNum in range(columns)] if idx < len(record.msg)]
                format = (len(indices) * (" %%-%ds " % columnWidth))
                returns.append(format % tuple([record.msg[idx] for idx in indices]))
        #elif type(record.msg) == lxml.etree._Element:
        #    returns.append(str(xml_print(record.msg)))
        else:
            returns.append(str(record.msg))
        if record.exc_info:
            returns.append(self.formatException(record.exc_info))
        return '\n'.join(returns)

class FragmentingSysLogHandler(logging.handlers.SysLogHandler):
    '''This handler fragments messages into chunks smaller than 250 characters'''

    def __init__(self, procname, path, facility):
        self.procname = procname
        self.unixsocket = False
        logging.handlers.SysLogHandler.__init__(self, path, facility)

    def emit(self, record):
        '''chunk and deliver records'''
        record.name = self.procname
        if str(record.msg) > 250:
            msgs = []
            error = record.exc_info
            record.exc_info = None
            msgdata = record.msg
            while msgdata:
                newrec = copy.deepcopy(record)
                newrec.msg = msgdata[:250]
                msgs.append(newrec)
                msgdata = msgdata[250:]
            msgs[0].exc_info = error
        else:
            msgs = [record]
        while msgs:
            newrec = msgs.pop()
            msg = self.log_format_string % (self.encodePriority(self.facility,
                                                                newrec.levelname.lower()), self.format(newrec))
            try:
                self.socket.send(msg)
            except socket.error:
                while True:
                    try:
                        if isinstance(self.address, types.TupleType):
                            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        else:
                            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                        self.socket.connect(self.address)
                        break
                    except socket.error:
                        continue
                self.socket.send("Reconnected to syslog")
                self.socket.send(msg)

def setup_logging(procname, to_console=True, to_syslog=True, syslog_facility='daemon', level=0):
    '''setup logging for bcfg2 software'''
    if hasattr(logging, 'already_setup'):
        return 
    # add the handler to the root logger
    if to_console:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        # tell the handler to use this format
        console.setFormatter(TermiosFormatter())
        logging.root.addHandler(console)
    if to_syslog:
        try:
            try:
                syslog = FragmentingSysLogHandler(procname, '/dev/log', syslog_facility)
            except socket.error:
                syslog = FragmentingSysLogHandler(procname, ('localhost', 514), syslog_facility)
            syslog.setLevel(logging.DEBUG)
            syslog.setFormatter(logging.Formatter('%(name)s[%(process)d]: %(message)s'))
            logging.root.addHandler(syslog)
        except socket.error:
            logging.root.error("failed to activate syslogging")
        except:
            print "Failed to activate syslogging"
    logging.root.setLevel(level)
    logging.already_setup = True