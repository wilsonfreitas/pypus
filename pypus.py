#!/usr/bin/env python

import re
import types

def import_func(className, modName=None):
    if not modName:
        fields = className.split('.')
        modName = '.'.join(fields[:-1])
        className = fields[-1]
    if modName is '':
        modName = '__main__'
    module = __import__(modName, globals(), locals(), [className], -1)
    func = getattr(module, className)
    if type(func) is types.ModuleType:
        raise TypeError("Not callable object found")
    else:
        return func


class NameNotResolvedException(Exception):
    """docstring for NameNotResolvedException"""
    def __init__(self, message):
        super(NameNotResolvedException, self).__init__(message)
        self.message = message
    


class PypusParserError(Exception):
    pass


class PypusCode(object):
    """docstring for PypusCode"""
    def __init__(self, code):
        self.preproc_code = code
        self.posproc_code = ''
        
    def __len__(self):
        return len(self.posproc_code)
        
    def apply_macros(self, macros):
        for macro, value in macros:
            if macro in self.preproc_code:
                self.posproc_code = self.preproc_code.replace(macro, value)
                return
        self.posproc_code = self.preproc_code
    
    def __getitem__(self, key):
        if self.posproc_code is not '':
            return self.posproc_code[key]
        else:
            return self.preproc_code[key]
        


class PypusParser(object):
    """PypusParser"""
    def __init__(self):
        self.chunk_types = [
            ('ignore', re.compile(r'^[ \t]+'), lambda *args: None),
            ('func', re.compile(r'^(@([a-zA-Z_][a-zA-Z0-9_]*)(\.[a-zA-Z_][a-zA-Z0-9_]*)*)'), self._handle_func),
            ('placehdr', re.compile(r'^\$\{([^\\\}\{]|(\\.))+\}'), self._handle_placehdr),
            ('placehdr', re.compile(r'^\$(\d+)'), self._handle_placehdr),
            ('lparen', re.compile(r'^\('), self._handle_lparen),
            ('rparen', re.compile(r'^\)'), self._handle_rparen),
            ('lbrak', re.compile(r'^\{'), self._handle_lparen),
            ('rbrak', re.compile(r'^\}'), self._handle_rparen),
            ('lsqbrak', re.compile(r'^\['), self._handle_lparen),
            ('rsqbrak', re.compile(r'^\]'), self._handle_rparen),
            ('delim', re.compile(r'^[,:]'), self._handle_delim),
            ('pykwargs', re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*=)'), self._handle_pykwargs),
            ('pystr', re.compile(r'\"([^\\"]|(\\.))*\"'), self._handle_pyargs),
            ('pyargs', re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)'), self._handle_pyargs),
            ('pynum', re.compile(r'^(\d+(\.(\d+)?)?([eE]-?\d+)?)'), self._handle_pyargs),
            # ('pyargs', re.compile(r'^([^,\)\( \t\{\}\[\]]+)'), self._handle_pyargs),
        ]
    
    def parse(self, code, modNames):
        """docstring for parse"""
        self.current_function = None
        self.functions = []
        self.action_stack = []
        self.current_kwkey = None
        self.current_arg = ''
        i = 0
        k = 0
        while k < len(self.chunk_types):
            chunk_type = self.chunk_types[k]
            code_part = code[i:]
            m = chunk_type[1].match(code_part)
            if m:
                i += len(m.group())
                # print '%-15s [%s]' % (chunk_type[0], m.group())
                chunk_type[2](code_part, m)
                k = 0
            else:
                k += 1
        if not i == len(code):
            raise PypusParserError('Unknown code token: ' + code_part)        
        for func in self.functions:
            func.resolve(modNames)
        return self.functions
    
    def _handle_func(self, code_part, regex):
        """docstring for _handle_func"""
        self.current_function = PypusFunction(regex.group())
        self.functions.append(self.current_function)
    
    def _handle_placehdr(self, code_part, regex):
        """docstring for _handle_placehdr"""
        self.current_function.args.append(Placeholder(regex.group()))
        self.current_function.has_placeholder = True
    
    def _handle_lparen(self, code_part, regex):
        """docstring for _handle_lparen"""
        if len(self.action_stack) == 0:
            self.action_stack.append('function-args')
        else:
            self.action_stack.append('py-arg')
            self.current_arg += regex.group()
    
    def _handle_rparen(self, code_part, regex):
        """docstring for _handle_lparen"""
        action = self.action_stack.pop()
        if action == 'py-arg':
            self.current_arg += regex.group()
            if self.action_stack[-1] == 'function-args':
                self._define_arg()
    
    def _handle_delim(self, code_part, regex):
        """docstring for _handle_lparen"""
        action = self.action_stack[-1]
        delim = regex.group()
        if action == 'py-arg':
            self.current_arg += delim
    
    def _handle_pykwargs(self, code_part, regex):
        """docstring for _handle_pykwargs"""
        text = regex.group()
        self.current_kwkey = text[:-1]
    
    def _handle_pyargs(self, code_part, regex):
        """docstring for _handle_pyargs"""
        action = self.action_stack[-1]
        arg = regex.group()
        
        if action == 'py-arg':
            self.current_arg += arg
        elif action == 'function-args':
            self.current_arg = arg
            self._define_arg()
    
    def _define_arg(self):
        """docstring for define_arg"""
        print self.current_arg
        value = eval(self.current_arg)
        print value
        self.current_arg = ''
        if self.current_kwkey is not None:
            self.current_function.kwargs[self.current_kwkey] = value
            self.current_kwkey = None
        else:
            self.current_function.args.append(value)
    


class PypusFunction(object):
    def __init__(self, func_name):
        self.has_placeholder = False
        self.args = []
        self.kwargs = {}
        self.func_name = func_name[1:]
        self.func = None
    
    def resolve(self, modNames=set()):
        """docstring for resolve"""
        try:
            self.func = import_func(self.func_name)
        except (AttributeError, ImportError, TypeError):
            for modName in modNames:
                try:
                    self.func = import_func(self.func_name, modName)
                    break
                except (AttributeError, ImportError, TypeError):
                    pass
        if self.func is None:
            raise NameNotResolvedException("%s couldn't be resolved, check modules variable in the "
                                           "configuration file." % (self.func_name) )
    
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
    
    def __call__(self, S=None):
        """Execute the function"""
        if S is None:
            return self.func(*self.args, **self.kwargs)
        elif self.has_placeholder:
            args = [self._replace_placeholder(S, arg) for arg in self.args]
            kwargs = dict([(k, self._replace_placeholder(S, v)) for k,v in self.kwargs.iteritems()])
            return self.func(*args, **kwargs)
        else:
            return self.func(S, *self.args, **self.kwargs)
    


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
    
    def __str__(self):
        """docstring for __str__"""
        return self.arg
    
    def __repr__(self):
        """docstring for __repr__"""
        return self.arg
    


class Pypus(object):
    """docstring for Pypus"""
    def __init__(self, modules, macros):
        self.modules = modules
        self.macros = macros
    
    def execute(self, code, S=None):
        """Execute pypus code"""
        pypus_code = PypusCode(code)
        pypus_code.apply_macros(self.macros)
        parser = PypusParser()
        func_stack = parser.parse(pypus_code, set(self.modules))
        if S is None:
            func = func_stack.pop(0)
            S = func()
            while func_stack:
                func = func_stack.pop(0)
                S = func(S)
        else:
            while func_stack:
                func = func_stack.pop(0)
                S = func(S)
        return S
    

