# Code for CS 171, Winter, 2021

import Tree

verbose = False
def printV(*args):
    if verbose:
        print(*args)

# A Python implementation of the AIMA CYK-Parse algorithm in Fig. 23.5 (p. 837).
def CYKParse(words, grammar):
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
        for X, p in getGrammarLexicalRules(grammar, words[i]):
            P[X + '/' + str(i) + '/' + str(i)] = p
            T[X + '/' + str(i) + '/' + str(i)] = Tree.Tree(X, None, None, lexiconItem=words[i])
    printV('P:', P)
    printV('T:', [str(t)+':'+str(T[t]) for t in T])
    # Construct X_i:j from Y_i:j + Z_j+i:k, shortest spans first
    for i, j, k in subspans(len(words)):
        for X, Y, Z, p in getGrammarSyntaxRules(grammar):
            if Z:
                printV('i:', i, 'j:', j, 'k:', k, '', X, '->', Y, Z, '[' + str(p) + ']',
                       'PYZ =', getP(Y, i, j), getP(Z, j + 1, k), p, '=', getP(Y, i, j) * getP(Z, j + 1, k) * p)
                PYZ = getP(Y, i, j) * getP(Z, j+1, k) * p
                if PYZ > getP(X, i, k):
                    printV('     inserting from', i, '-', k, ' ', X, '->', T[Y + '/' + str(i) + '/' + str(j)],
                           T[Z + '/' + str(j + 1) + '/' + str(k)],
                           'because', PYZ, '=', getP(Y, i, j), '*', getP(Z, j + 1, k), '*', p, '>', getP(X, i, k), '=',
                           'getP(' + X + ',' + str(i) + ',' + str(k) + ')')
                    P[X + '/' + str(i) + '/' + str(k)] = PYZ
                    T[X + '/' + str(i) + '/' + str(k)] = Tree.Tree(X, T[Y + '/' + str(i) + '/' + str(j)],
                                                                  T[Z + '/' + str(j + 1) + '/' + str(k)])
            else:   # single category
                printV('i:', i, 'j:', j, 'k: -', '', X, '->', Y, '[' + str(p) + ']',
                       'PYZ =', getP(Y, i, j), p, '=', getP(Y, i, j) * p)
                PYZ = getP(Y, i, j) * p
                if PYZ > getP(X, i, k):
                    printV('     inserting from', i, '-', j, ' ', X, '->', T[Y + '/' + str(i) + '/' + str(j)],
                           'because', PYZ, '=', getP(Y, i, j), '*', p, '>', getP(X, i, j), '=',
                           'getP(' + X + ',' + str(i) + ',' + str(j) + ')')
                    P[X + '/' + str(i) + '/' + str(j)] = PYZ
                    T[X + '/' + str(i) + '/' + str(j)] = Tree.Tree(X, T[Y + '/' + str(i) + '/' + str(j)], None)
    printV('T:', [str(t)+':'+str(T[t]) for t in T])
    return T, P

# Python uses 0-based indexing, requiring some changes from the book's
# 1-based indexing: i starts at 0 instead of 1
def subspans(N):
    for length in range(2, N+1):
        for i in range(N+1 - length):
            k = i + length - 1
            for j in range(i, k):
                yield i, j, k

# These two getXXX functions use yield instead of return so that a single pair can be sent back,
# and since that pair is a tuple, Python permits a friendly 'X, p' syntax
# in the calling routine.
def getGrammarLexicalRules(grammar, word):
    for rule in grammar['lexicon']:
        if rule[1] == word:
            yield rule[0], rule[2]

def getGrammarSyntaxRules(grammar):
    rulelist = []
    for rule in grammar['syntax']:
        yield rule[0], rule[1], rule[2], rule[3]


# Sample sentences:
# Hi, I am Peter. I am Peter. Hi, my name is Peter. My name is Peter.
# What is the temperature in Irvine? What is the temperature in Irvine now?
# What is the temperature in Irvine tomorrow?
#
def getGrammarWeather():
    return {
        'syntax' : [
            ['S', 'Greeting', 'S', 0.1],
            ['S', 'NP', 'VP', 0.3],
            ['S', 'WQuestion', 'VP', 0.2],

            # new rules
            ['S', 'WQuestion', 'S', 0.1],
            ['S', 'AdverbPhrase', 'VP', 0.1],
            ['S', 'S', 'AdverbPhrase', 0.2],
            # end

            ['VP', 'Verb', 'Name', 0.1],

            # new rules
            ['VP', 'VP', 'NP', 0.3],
            ['VP', 'VP', 'NP+AdverbPhrase', 0.2],
            ['VP', 'Verb', '', 0.3],
            ['VP', 'Verb', 'Adjective', 0.1],
            # end

            ['NP', 'Article', 'Noun', 0.2],
            ['NP', 'Adjective', 'Noun', 0.2],

            # new rules
            ['NP', 'Pronoun', '', 0.2],
            ['NP', 'Noun', '', 0.2],
            ['NP', 'Name', '', 0.2],
            # end

            ['NP+AdverbPhrase', 'AdverbPhrase', 'NP', 0.4],
            ['NP+AdverbPhrase', 'NP', 'AdverbPhrase', 0.4],

            # new rule
            ['NP+AdverbPhrase', 'AdverbPhrase', 'NP+AdverbPhrase', 0.2],

            ['AdverbPhrase', 'Preposition', 'NP', 0.2],
            ['AdverbPhrase', 'Preposition', 'Name', 0.2],
            ['AdverbPhrase', 'Adverb', 'AdverbPhrase', 0.2],
            ['AdverbPhrase', 'AdverbPhrase', 'Adverb', 0.2],

            # new rules
            ['AdverbPhrase', 'Adverb', '', 0.2],
            ['AdverbPhrase', 'Adverb', 'VP', 0.2],
            ['AdverbPhrase', 'Preposition', 'Adverb', 0.2],
            # end
        ],
        'lexicon' : [
            ['Greeting', 'hi', 0.5],
            ['Greeting', 'hello', 0.5],
            ['WQuestion', 'what', 0.5],
            ['WQuestion', 'when', 0.2],
            ['WQuestion', 'which', 0.2],
            ['WQuestion', 'will', 0.2],
            ['Verb', 'am', 0.3],
            ['Verb', 'is', 0.3],
            ['Name', 'Peter', 0.2],
            ['Name', 'Sue', 0.2],
            ['Name', 'Irvine', 0.2],
            ['Pronoun', 'I', 1.0],
            ['Noun', 'man', 0.2],
            ['Noun', 'name', 0.2],
            ['Noun', 'temperature', 0.6],
            ['Article', 'the', 0.7],
            ['Article', 'a', 0.3],
            ['Adjective', 'my', 0.5],
            ['Adverb', 'now', 0.25],
            ['Adverb', 'today', 0.25],
            ['Adverb', 'tomorrow', 0.25],
            ['Preposition', 'with', 0.33],
            ['Preposition', 'in', 0.33],

            # step 5.1
            ['Verb', 'was', 0.2],
            ['Adverb', 'yesterday', 0.25],
            ['Name', 'Tustin', 0.2],
            ['Name', 'Pasadena', 0.2],

            # step 5.2
            ['Verb', 'be', 0.2],
            ['Preposition', 'than', 0.33],
            ['Adjective', 'hotter', 0.25],
            ['Adjective', 'colder', 0.25],
         ]
    }

# Unit testing code
if __name__ == '__main__':
    verbose = True
    # CYKParse(['the', 'wumpus', 'is', 'dead'], getGrammarE0())
    #CYKParse(['the', 'old', 'man', 'the', 'boat'], getGrammarGardenPath())
    #CYKParse(['I', 'saw', 'a', 'man', 'with', 'my', 'telescope'], getGrammarTelescope())
    # CYKParse(['my', 'name', 'is', 'Peter'], getGrammarWeather())
    # CYKParse(['hi', 'I', 'am', 'Peter'], getGrammarWeather())
    # CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine'], getGrammarWeather())
    # CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'now'], getGrammarWeather())
    # CYKParse(['what', 'is', 'the', 'temperature', 'now', 'in', 'Irvine'], getGrammarWeather())
    # CYKParse(['what', 'is', 'now', 'the', 'temperature', 'in', 'Irvine'], getGrammarWeather())
    # CYKParse(['I', 'am', 'Peter'], getGrammarWeather())

    # step 5 testing
    # CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'yesterday'], getGrammarWeather())
    # CYKParse(['what', 'was', 'now', 'the', 'temperature', 'in', 'Irvine'], getGrammarWeather())
    # CYKParse(['what', 'was', 'the', 'temperature', 'in', 'Irvine', 'now'], getGrammarWeather())
    # CYKParse(['what', 'was', 'the', 'temperature', 'in', 'Irvine', 'yesterday'], getGrammarWeather())
    # CYKParse(['what', 'was', 'the', 'temperature', 'in', 'Irvine', 'tomorrow'], getGrammarWeather())
    # CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'tomorrow'], getGrammarWeather())

    CYKParse("will tomorrow be hotter than today in Irvine".split(), getGrammarWeather())




# Hi, I am Peter. I am Peter. Hi, my name is Peter. My name is Peter.
# What is the temperature in Irvine? What is the temperature in Irvine now?
# What is the temperature in Irvine tomorrow?
