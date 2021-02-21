# Code for CS 171, Winter, 2021

import Tree

class VacationParser:
    def __init__(self):
        self.verbose = False
        self.weatherGrammar = {
            'syntax' : [
                ['S', 'NP', 'VP', 0.3],
                ['S', 'WQuestion', 'VP', 0.2],

                ['S', 'WQuestion', 'S', 0.1],
                ['S', 'AdverbPhrase', 'VP', 0.1],
                ['S', 'S', 'AdverbPhrase', 0.2],

                ['VP', 'Verb', 'Noun', 0.1],
                ['VP', 'VP', 'NP', 0.2],
                ['VP', 'VP', 'NP+AdverbPhrase', 0.2],
                ['VP', 'Verb', '', 0.3],
                ['VP', 'Verb', 'Adjective', 0.1],

                ['VP', 'AuxVP', 'NP', 0.2],
                ['AuxVP', 'AuxVerb', 'VP', 0.7],
                ['AuxVP', 'AuxVerb', 'Verb', 0.3],

                ['NP', 'Article', 'Noun', 0.2],
                ['NP', 'Adjective', 'Noun', 0.2],
                ['NP', 'Pronoun', '', 0.2],
                ['NP', 'Noun', '', 0.2],
                ['NP', 'Name', '', 0.2],

                ['NP+AdverbPhrase', 'AdverbPhrase', 'NP', 0.4],
                ['NP+AdverbPhrase', 'NP', 'AdverbPhrase', 0.4],

                ['NP+AdverbPhrase', 'AdverbPhrase', 'NP+AdverbPhrase', 0.2],

                ['AdverbPhrase', 'Preposition', 'NP', 0.2],
                ['AdverbPhrase', 'Preposition', 'Noun', 0.1],
                ['AdverbPhrase', 'Adverb', 'AdverbPhrase', 0.2],
                ['AdverbPhrase', 'AdverbPhrase', 'Adverb', 0.2],

                ['AdverbPhrase', 'Adverb', '', 0.2],
                ['AdverbPhrase', 'Adverb', 'VP', 0.2],
                ['AdverbPhrase', 'Adverb', 'Verb', 0.1],
                ['AdverbPhrase', 'Preposition', 'Adverb', 0.1],
            ],
            'lexicon' : [
                ['WQuestion', 'what', 0.2],
                ['WQuestion', 'when', 0.2],
                ['WQuestion', 'where', 0.2],
                ['WQuestion', 'which', 0.1],
                ['WQuestion', 'will', 0.1],
                ['WQuestion', 'could', 0.1],
                ['WQuestion', 'should', 0.1],
                ['WQuestion', 'how', 0.1],

                ['Verb', 'is', 0.2],
                ['Verb', 'be', 0.2],
                ['Verb', 'go', 0.4],

                # activities
                ['Verb', 'surf', 0.02],
                ['Verb', 'ski', 0.02],
                ['Verb', 'sled', 0.02],
                ['Verb', 'snowboard', 0.02],
                ['Verb', 'kayak', 0.02],
                ['Verb', 'fish', 0.02],
                ['Verb', 'dive', 0.02],
                ['Verb', 'golf', 0.02],
                ['Verb', 'sail', 0.02],
                ['Verb', 'skydive', 0.02],
                ['Verb', 'hike', 0.02],

                ['Adverb', 'now', 0.3],
                ['Adverb', 'today', 0.3],
                ['Adverb', 'tomorrow', 0.3],
                ['Adverb', 'scuba', 0.1],

                ['Pronoun', 'I', 0.8],
                ['Pronoun', 'we', 0.2],
                ['Noun', 'man', 0.1],
                ['Noun', 'temperature', 0.1],
                ['Noun', 'weather', 0.2],
                ['Noun', 'Irvine', 0.2],

                # activities
                ['Noun', 'surfing', 0.01],
                ['Noun', 'skiing', 0.01],
                ['Noun', 'sledding', 0.01],
                ['Noun', 'snowboarding', 0.01],
                ['Noun', 'kayaking', 0.01],
                ['Noun', 'fishing', 0.01],
                ['Noun', 'diving', 0.01],
                ['Noun', 'golfing', 0.01],
                ['Noun', 'sailing', 0.01],
                ['Noun', 'skydiving', 0.01],
                ['Noun', 'hiking', 0.01],

                ['Article', 'the', 0.7],
                ['Article', 'a', 0.3],
                ['Adjective', 'my', 0.5],
                ['Adjective', 'scuba', 0.1],

                ['Preposition', 'with', 0.33],
                ['Preposition', 'in', 0.33],
                ['Preposition', 'than', 0.33],
                ['Adjective', 'hotter', 0.1],
                ['Adjective', 'colder', 0.1],
                ['Adjective', 'warmer', 0.1],
                ['Adjective', 'cooler', 0.1],
            ]
        }

    def printV(self, *args):
        if self.verbose:
            print(*args)

    # A Python implementation of the AIMA CYK-Parse algorithm in Fig. 23.5 (p. 837).
    def CYKParse(self, words, grammar):
        T = {}
        P = {}
        # Instead of explicitly initializing all P[X, i, k] to 0, store
        # only non-0 keys, and use this helper function to return 0 as needed.
        def getP(X, i, k):
            key = str(X) + '/' + str(i) + '/' + str(k)
            if key in P:
                return P[key]
            else:
                return 0
        # Insert lexical categories for each word
        for i in range(len(words)):
            for X, p in self.getGrammarLexicalRules(grammar, words[i]):
                P[X + '/' + str(i) + '/' + str(i)] = p
                T[X + '/' + str(i) + '/' + str(i)] = Tree.Tree(X, None, None, lexiconItem=words[i])
        self.printV('P:', P)
        self.printV('T:', [str(t)+':'+str(T[t]) for t in T])
        # Construct X_i:j from Y_i:j + Z_j+i:k, shortest spans first
        for i, j, k in self.subspans(len(words)):
            for X, Y, Z, p in self.getGrammarSyntaxRules(grammar):
                if Z:
                    self.printV('i:', i, 'j:', j, 'k:', k, '', X, '->', Y, Z, '[' + str(p) + ']',
                           'PYZ =', getP(Y, i, j), getP(Z, j + 1, k), p, '=', getP(Y, i, j) * getP(Z, j + 1, k) * p)
                    PYZ = getP(Y, i, j) * getP(Z, j+1, k) * p
                    if PYZ > getP(X, i, k):
                        self.printV('     inserting from', i, '-', k, ' ', X, '->', T[Y + '/' + str(i) + '/' + str(j)],
                               T[Z + '/' + str(j + 1) + '/' + str(k)],
                               'because', PYZ, '=', getP(Y, i, j), '*', getP(Z, j + 1, k), '*', p, '>', getP(X, i, k), '=',
                               'getP(' + X + ',' + str(i) + ',' + str(k) + ')')
                        P[X + '/' + str(i) + '/' + str(k)] = PYZ
                        T[X + '/' + str(i) + '/' + str(k)] = Tree.Tree(X, T[Y + '/' + str(i) + '/' + str(j)],
                                                                      T[Z + '/' + str(j + 1) + '/' + str(k)])
                else:   # single category
                    self.printV('i:', i, 'j:', j, 'k: -', '', X, '->', Y, '[' + str(p) + ']',
                           'PYZ =', getP(Y, i, j), p, '=', getP(Y, i, j) * p)
                    PYZ = getP(Y, i, j) * p
                    if PYZ > getP(X, i, k):
                        self.printV('     inserting from', i, '-', j, ' ', X, '->', T[Y + '/' + str(i) + '/' + str(j)],
                               'because', PYZ, '=', getP(Y, i, j), '*', p, '>', getP(X, i, j), '=',
                               'getP(' + X + ',' + str(i) + ',' + str(j) + ')')
                        P[X + '/' + str(i) + '/' + str(j)] = PYZ
                        T[X + '/' + str(i) + '/' + str(j)] = Tree.Tree(X, T[Y + '/' + str(i) + '/' + str(j)], None)
        # self.printV('T:', [str(t)+':'+str(T[t]) for t in T])
        self.printV('Tree ----------------------------------------------------------------------------------------------')
        for t in T:
            self.printV(f"{t}: {T[t]}")
        return T, P

    # Python uses 0-based indexing, requiring some changes from the book's
    # 1-based indexing: i starts at 0 instead of 1
    def subspans(self, N):
        for length in range(2, N+1):
            for i in range(N+1 - length):
                k = i + length - 1
                for j in range(i, k):
                    yield i, j, k

    # These two getXXX functions use yield instead of return so that a single pair can be sent back,
    # and since that pair is a tuple, Python permits a friendly 'X, p' syntax
    # in the calling routine.
    def getGrammarLexicalRules(self, grammar, word):
        for rule in grammar['lexicon']:
            if rule[1].lower() == word.lower():
                yield rule[0], rule[2]

    def getGrammarSyntaxRules(self, grammar):
        rulelist = []
        for rule in grammar['syntax']:
            yield rule[0], rule[1], rule[2], rule[3]

    def getGrammarWeather(self):
        return self.weatherGrammar

    def setVerbose(self, val: bool):
        self.verbose = val

    # There is space for about 300 cities, and a probability of 0.3 is divided among them.
    # All cities are in California only
    def addLexicon(self, city):
        self.weatherGrammar["lexicon"].append(
            ["Noun", city, 0.3 / 300]
        )


# Unit testing code
if __name__ == '__main__':
    c = VacationParser()
    c.setVerbose(True)

    c.CYKParse("SHOULD I GO SCUBA DIVING".split(), c.getGrammarWeather())




# Hi, I am Peter. I am Peter. Hi, my name is Peter. My name is Peter.
# What is the temperature in Irvine? What is the temperature in Irvine now?
# What is the temperature in Irvine tomorrow?
