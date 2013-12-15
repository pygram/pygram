import pydot.pydot as pydot

import modply
import re

from parser import GrammarParser, ServerTimeOut

class LRAutomaton(object):
    '''
     Object to keep the information of the automaton built by some
     parsing method.
    '''

    def __init__(self,lr):
        '''
         Takes an instance of PLYs LRGeneratedTable and builds an automaton.
        '''
        self.augmented_grammar = tuple(enumerate(str(p) for p in lr.grammar.Productions))
        self.reduce_rules = []
        for i,p in enumerate(lr.grammar.Productions):
            rule = str(p)
            rule = rule.split('->')
            rule = (i,rule[0].rstrip(' ').lstrip(' '),sum(1 for r in rule[1].split(' ') if len(r) > 0 and "<empty>" != r))
            self.reduce_rules.append(rule)
        self.kernel = lr.automaton_kernel
        self.kernel_str = {}
        for k,v in self.kernel.items():
            productions = sorted(((n,prod[0],prod[1]) for n,prod in v.items()),key=lambda x: x[0])
            productions_str = ('{0}, {1}'.format(prod,'/'.join(lookaheads)) if len(lookaheads) > 0 else prod for num,prod,lookaheads in productions)
            self.kernel_str[k] = '\n'.join(productions_str)

        # A negative number means a reduction action is to be taken; taking its absolute
        # value results in the number that enumerates the production used to reduce. 
        # A number equal to 0 means the string is to be accepted.
        self.action = lr.lr_action

        self.goto = lr.lr_goto
        self.rr_conflicts = lr.rr_conflicts
        self.sr_conflicts = lr.sr_conflicts
        self.first = lr.grammar.compute_first()
        self.follow = lr.grammar.compute_follow()
        self.nonterminals = lr.grammar.Nonterminals
        self.terminals = list(t for t in lr.grammar.Terminals if 'error' != t)
        self.terminals.append('$end')

    def to_svg(self):
        '''
         Uses pydot to create an SVG representation of the automaton.
        '''

        graph = pydot.Dot(graph_type='digraph')
        graph.set_node_defaults(shape='plaintext',style="filled")

        nodes = {}
        for st,kernel in self.kernel_str.items():
            nodes[st] = pydot.Node(name="{0}".format(st),label="State {0}\n{1}".format(st,kernel.replace('$end','$')))
        
        nodes['acc'] = pydot.Node(name="acc",label="acc")

        for st,node in nodes.items():
            graph.add_node(node)

        for st,tran in self.action.items():
            for sym,num in tran.items():
                if num >= 0:
                    if num == 0:
                        graph.add_edge(pydot.Edge(nodes[st],nodes['acc'],label=sym.replace('$end','$')))
                    else:
                        graph.add_edge(pydot.Edge(nodes[st],nodes[num],label=sym.replace('$end','$')))

        for st,tran in self.goto.items():
            for sym,num in tran.items():
                graph.add_edge(pydot.Edge(nodes[st],nodes[num],label=sym))

        return re.sub(r'<\?xml.+\?>\s+<\!DOCTYPE[^>]+>','',graph.create_svg().decode('utf8'))

def create_grammar(terminals,productions,start=None):
    '''
     Returns a PLY grammar object initialized
     with a set of productions; or None if the
     provided data results in a grammar error.
    '''

    if start is None:
        start = productions[0][0]

    errors = []
    warnings = []

    # Check that terminals are valid.
    if 'error' in terminals:
        errors.append('Invalid terminal: error')
    else:
        # Try to create the grammar object.
        grammar = modply.Grammar(terminals)
        try:
            for production in productions:
                head = production[0]
                body = production[1:]
                grammar.add_production(head,body)
            grammar.set_start(start)
        except modply.GrammarError as e:
            errors.append('Grammar error: {0}'.format(str(e)))
        else:
            # Existence of undefined symbols is an error.
            undefined = grammar.undefined_symbols()
            for sym, prod in undefined:
                errors.append('Undefined symbol: {0}'.format(sym))

            # Are there infinite loops?
            infinite = grammar.infinite_cycles()
            for sym in infinite:
                errors.append('Infinite recursion detected for symbol: {0}'.format(sym))

            # Are there unused terminals?
            unused = grammar.unused_terminals()
            for sym in unused:
                warnings.append('Unused terminal: {0}'.format(sym))

            # Are all symbols reachable?
            unreachable = grammar.find_unreachable()
            for sym in unreachable:
                warnings.append('Unreachable symbol: {0}'.format(sym))

            # Are there unused productions?
            unused = grammar.unused_rules()
            for prod in unused:
                warnings.append('Unused production: {0}'.format(str(prod)))
    
    if len(errors) > 0:
        grammar = None

    return grammar,warnings,errors

def create_automaton(terminals,productions,start=None,method='LALR'):
    '''
     Uses PLYs capabilites to get an SLR or LALR
     parsing table from which the automaton is
     extracted.
    '''

    # We're using the GrammarParser.mutex static variable in this context
    # because the analysis of the grammar is made by PLYs machinery,
    # so we need to protect ply.yacc state.

    if GrammarParser.mutex.acquire(True,15): 
 
        grammar,warnings,errors = create_grammar(terminals,productions,start)
     
        if not grammar is None:
            if method not in ('SLR','LALR'):
                errors.append('Unsupported parsing method: {0}'.format(method))
                GrammarParser.mutex.release()
            else:
                try:
                    lr = modply.LRGeneratedTable(grammar,method)

                    # Are there any conflicts?
                    for state,symbol,resolution in lr.sr_conflicts:
                        warnings.append('Shift/Reduce conflict for "{0}" in state {1} resolved as "{2}".'.format(symbol,state,resolution))
                    for state,symbol,rejected in lr.rr_conflicts:
                        warnings.append('Reduce/Reduce conflict in state {1} resolved using "{0}", rejected rule "{2}".'.format(symbol,state,rejected))

                    automaton = LRAutomaton(lr) 

                except modply.LALRError as e:
                    errors.append('Bad input: the grammar results in an "{0}".'.format(str(e)))
                finally:
                    GrammarParser.mutex.release()

        else:
            GrammarParser.mutex.release()

        if len(errors) > 0:
            automaton = None

        return automaton,warnings,errors

    else:
        raise ServerTimeOut('Server busy: please try again in a few seconds.')

if __name__ == '__main__':
    main()
