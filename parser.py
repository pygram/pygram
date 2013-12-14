import ply.lex as lex
import ply.yacc as yacc

import threading
 
class GrammarSyntaxError(Exception): 
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class ServerTimeOut(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
 
class GrammarLexer(object):
 
    tokens = ('SYMBOL','COLON','SEMICOLON','PIPE')

    t_SYMBOL = r'[a-zA-Z][a-zA-Z0-9]*'
    t_COLON = r'[\:]'
    t_SEMICOLON = r'[\;]'
    t_PIPE = r'[\|]'

    t_ignore = '\b\t\f\r\n '

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def t_error(self, t):
        t.lexer.skip(1)

class GrammarParser(object):

    # We need a lock to protect ply.yacc state,
    # in case multiple Flask threads need to parse.
    mutex = threading.Lock()

    def __init__(self):
        self.lexer = GrammarLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self,write_tables=1,debug=False)

    def p_start(self, p):
        'start : grammar'
        p[0] = tuple(tuple(production) for production in p[1])

    def p_grammar_start(self, p):
        'grammar : productions'
        p[0] = p[1]

    def p_grammar(self, p):
        'grammar : grammar productions'
        # A grammar is a list of productions.
        p[0] = p[1] + p[2]

    def p_productions(self, p):
        'productions : SYMBOL COLON productionRules'
        # A list of productions sharing the same right side.
        productions = []
        for rule in p[3]:
            rule.insert(0,p[1])
            productions.append(rule)
        p[0] = productions

    def p_production_rules1(self, p):
        'productionRules : rules SEMICOLON'
        p[0] = p[1]

    def p_production_rules2(self, p):
        'productionRules : rules PIPE SEMICOLON'
        p[1].append([]) # Add an empty production rule.
        p[0] = p[1]

    def p_production_rules3(self, p):
        'productionRules : SEMICOLON'
        p[0] = [[]] # An empty production rule.

    def p_rules_start(self, p):
        'rules : rule'
        p[0] = [p[1]]

    def p_rules(self, p):
        'rules : rules PIPE rule'
        p[1].append(p[3])
        p[0] = p[1]

    def p_rule_start(self, p):
        'rule : SYMBOL'
        p[0] = [p[1]]

    def p_rule(self, p):
        'rule : rule SYMBOL'
        p[1].append(p[2])
        p[0] = p[1]
 
    def p_error(self, p):
        raise GrammarSyntaxError('Bad input: grammar specification has syntax errors.')

    def parse(self, text):
   
        # Try to parse the input (waiting a max of 15 seconds). 
        if self.mutex.acquire(True,15): 
            try:
                retval = self.parser.parse(text, self.lexer.lexer, 0, 0, None)
            except GrammarSyntaxError as e:
                raise e
            finally:
                self.mutex.release()
            return retval
        else:
            raise ServerTimeOut('Server busy: please try again in a few seconds.')
