#!/usr/bin/env python


def _is(s, func):
    try:
        func(s)
    except ValueError:
        return False
    else:
        return True


def is_int(s):
    return _is(s, int)


def is_float(s):
    return _is(s, float)


class PypusParser(object):
    """PypusParser"""
    chunk_types = ['func', 'space', 'placehdr', 'lplacehdr', 'rplacehdr',
                   'lparen', 'rparen', 'delim', 'number', 'sdelim', 'var']
    
    chunk_pattern_table = {
        'func': re.compile(r'^(@[\w\.]+)'),
        'space': re.compile(r'^(\s+)'),
        'placehdr': re.compile(r'^\$[^{]'),
        'lplacehdr': re.compile(r'^\${'),
        'rplacehdr': re.compile(r'^}'),
        'lparen': re.compile(r'^\('),
        'rparen': re.compile(r'^\)'),
        'delim': re.compile(r'^[,:=]'),
        'number': re.compile(r'^(-?\d+\.?(\d+)?j?)'),
        'sdelim': re.compile(r'^"'),
        'var': re.compile(r'^([a-zA-Z_][a-zA-Z_0-9]+)')
    }
    
    def __init__(self, code):
        self.code = code
#     
# 
# def pypus_parser(code):
#     i = 0
#     chunk = code[i:]
#     while chunk:
#         if re.match(r'^(@[a-zA-Z\d\._]+)', chunk):
#             
#         chunk = code[i:]


def itertokens(code):
    i = code.find('@')
    j = code.find('@', i+1)
    
    while j >= 0:
        yield code[i:j].strip()
        i = j
        j = code.find('@', j+1)
        
    yield code[i:].strip()


def import_func(className, modName=None, module=None):
    if not module:
        if not modName:
            fields = className.split('.')
            modName = '.'.join(fields[:-1])
            className = fields[-1]
        if modName is '':
            modName = '__main__'
        module = __import__(modName, globals(), locals(), [className], -1)
        
    return getattr(module, className)


class Placeholder(object):
    def __init__(self, arg):
        self.arg = arg
        if arg is '$':
            self.index = None
        elif arg.startswith('${') and arg.endswith('}'):
            _range = arg[1:].strip('{}')
            if _range.find(':') > 0:
                begin, end = [int(i) for i in _range.split(':')]
                self.index = tuple(xrange(begin, end))
            else:
                self.index = tuple(eval('[' + _range + ']'))
        else:
            self.index = int(arg[1:])
    


class FunctionWrapper(object):
    def __init__(self, code):
        self.has_placeholder = False
        self.code = code
        func_name = code[1:]
        par_index = func_name.find('(')
        if par_index > 0:
            par = func_name[par_index:]
            func_name = func_name[:par_index]
        else:
            par = None
        self.func = import_func(func_name)
        if par:
            par = par.strip('()')
            # this parse of arguments isn't prepared to receive sequence types
            self.args   = self.parse_args(s.strip() for s in par.split(',') if s.find('=') < 0)
            self.kwargs = self.parse_kwargs(s.strip() for s in par.split(',') if s.find('=') > 0)
        else:
            self.args   = []
            self.kwargs = {}
    
    def _replace_placeholder(self, S, arg):
        """docstring for _replace_placeholder"""
        import numpy
        if type(arg) is Placeholder:
            if arg.index is None:
                return S
            elif type(arg.index) is tuple:
                args = []
                for i in arg.index:
                    args.append(S[:,i])
                return numpy.array(zip(*args))
            elif type(arg.index) is int:
                return S[:,arg.index]
        else:
            return arg
    
    def parse_arg(self, arg):
        """Parse atomic arguments passed to wrapped functions"""
        if is_int(arg):
            return int(arg)
        elif is_float(arg):
            return float(arg)
        elif arg in ('True', 'False', 'None'):
            return eval(arg)
        elif arg.startswith('$'):
            self.has_placeholder = True
            return Placeholder(arg)
        else:
            return arg
    
    def parse_args(self, args):
        """Generates a tuple with the parsed arguments"""
        return tuple(self.parse_arg(arg) for arg in args)
    
    def parse_kwarg(self, kwarg):
        """Generates a tuple with key value pairs separated by '='"""
        key, val = kwarg.split('=')
        key.strip()
        val.strip()
        return key, self.parse_arg(val)
    
    def parse_kwargs(self, kwargs):
        """Generates a dict with the keyword arguments"""
        return dict(self.parse_kwarg(kwarg) for kwarg in kwargs)
    
    def __call__(self, S):
        """Execute the function"""
        # return self.func(S)
        if self.has_placeholder:
            args = [self._replace_placeholder(S, arg) for arg in self.args]
            return self.func(*args, **self.kwargs)
        else:
            return self.func(S, *self.args, **self.kwargs)
    
            
def execute(S, code):
    """Execute pypus code"""
    func_stack = [FunctionWrapper(token) for token in itertokens(code)]
    func_stack.reverse()
    
    while func_stack:
        func = func_stack.pop()
        S = func(S)
        
    return S
