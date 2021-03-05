import Tree
from typing import List

class VacationParser:
    # hardcoded list of top 100 cities in California (from Wikipedia)
    # CITY_NAMES = {
    #     "los angeles", "san diego", "san jose", "san francisco", "fresno",
    #     "sacramento", "long beach", "oakland", "bakersfield", "anaheim",
    #     "santa ana", "riverside", "stockton", "irvine", "chula vista",
    #     "fremont", "san bernardino", "modesto", "fontana", "moreno valley",
    #     "santa clarita", "oxnard", "glendale", "huntington beach", "ontario",
    #     "rancho cucamonga", "santa rosa", "oceanside", "elk grove", "garden grove",
    #     "corona", "hayward", "lancaster", "salinas", "palmdale",
    #     "sunnyvale", "pomona", "escondido", "torrance", "roseville",
    #     "pasadena", "orange", "fullerton", "visalia", "santa clara",
    #     "concord", "thousand oaks", "simi valley", "victorville", "vallejo",
    #     "berkeley", "fairfield", "murrieta", "el monte", "carlsbad",
    #     "temecula", "clovis", "costa mesa", "antioch", "downey",
    #     "richmond", "jurupa valley", "ventura", "inglewood", "santa maria",
    #     "daly city", "west covina", "san mateo", "norwalk", "rialto",
    #     "chico", "el cajon", "burbank", "vista", "vacaville",
    #     "san marcos", "hesperia", "compton", "menifee", "tracy",
    #     "mission viejo", "chino", "south gate", "redding", "indio",
    #     "carson", "santa barbara", "westminster", "santa monica", "livermore",
    #     "san leandro", "citrus heights", "hawthorne", "redwood city", "lake forest",
    #     "hemet", "whittier", "newport beach", "milpitas", "chino hills"
    # }

    # City names that are one word long
    CITY_NAMES = {
        'hesperia', 'rialto', 'escondido', 'ontario', 'riverside',
        'berkeley', 'fontana', 'richmond', 'clovis', 'inglewood',
        'glendale', 'burbank', 'victorville', 'compton', 'redding',
        'irvine', 'oxnard', 'sunnyvale', 'corona', 'chino',
        'westminster', 'oceanside', 'milpitas', 'vista', 'concord',
        'hemet', 'oakland', 'downey', 'palmdale', 'pomona',
        'orange', 'carson', 'visalia', 'fresno', 'chico',
        'fremont', 'menifee', 'bakersfield', 'antioch', 'whittier',
        'modesto', 'carlsbad', 'livermore', 'vacaville', 'pasadena',
        'murrieta', 'roseville', 'anaheim', 'temecula', 'stockton',
        'norwalk', 'sacramento', 'hayward', 'salinas', 'lancaster',
        'torrance', 'hawthorne', 'tracy', 'fairfield',
        'vallejo', 'indio', 'ventura', 'fullerton'}

    # Some cities are two words long, so we have to join the prefix and suffix.
    # Note that not all combinations of prefix+suffix are valid cities
    CITY_PREFIXES = {
        'santa', 'newport', 'west', 'long', 'daly',
        'mission', 'costa', 'elk', 'redwood', 'citrus',
        'rancho', 'lake', 'chula', 'simi', 'jurupa',
        'moreno', 'thousand', 'huntington', 'south',
        'san', 'garden', 'los', 'chino', 'el'
    }

    CITY_SUFFIXES = {
        'bernardino', 'beach', 'covina', 'mesa', 'forest',
        'city', 'clara', 'jose', 'marcos', 'clarita',
        'viejo', 'francisco', 'cucamonga', 'rosa', 'mateo',
        'leandro', 'ana', 'diego', 'monte', 'vista', 'maria',
        'hills', 'valley', 'cajon', 'angeles', 'grove',
        'oaks', 'gate', 'heights', 'barbara', 'monica'
    }

    def __init__(self):
        self.verbose = False
        self.weatherGrammar = {
            'syntax' : [
                ['S', 'NP', 'VP', 0.1],
                ['S', 'NP', 'Verb', 0.05],
                ['S', 'Noun', 'VP', 0.05],
                ['S', 'WQuestion', 'VP', 0.2],
                ['S', 'WQuestion', 'S', 0.1],
                ['S', 'AdverbPhrase', 'VP', 0.1],
                ['S', 'S', 'PrepPhrase', 0.1],
                ['S', 'Noun', 'Verb', 0.05],
                ['S', 'Pronoun', 'Verb', 0.05],

                ['VP', 'VP', 'NP', 0.2],
                ['VP', 'VP', 'NP+AdverbPhrase', 0.05],
                ['VP', 'VP', 'AdverbPhrase', 0.05],
                ['VP', 'VP', 'Adverb', 0.05],
                ['VP', 'Verb', 'Noun', 0.1],
                ['VP', 'Verb', 'VP', 0.1],
                ['VP', 'Verb', '', 0.2],
                ['VP', 'Verb', 'Adjective', 0.1],
                ['VP', 'AuxVerb', 'VP', 0.07],
                ['VP', 'AuxVerb', 'Verb', 0.03],
                ['VP', 'Adverb', 'VP', 0.1],
                ['VP', 'Adverb', 'Verb', 0.1],

                ['NP', 'Article', 'Noun', 0.1],
                ['NP', 'Adjective', 'Noun', 0.2],
                ['NP', 'Pronoun', '', 0.1],
                ['NP', 'Noun', '', 0.2],
                ['NP', 'Det', 'Noun', 0.1],
                ['NP', 'Name', '', 0.2],
                ['NP', 'CityName', '', 0.2],
                ['CityName', 'CityPrefix', 'CitySuffix', 1.0],

                ['NP+AdverbPhrase', 'AdverbPhrase', 'NP', 0.4],
                ['NP+AdverbPhrase', 'NP', 'AdverbPhrase', 0.4],
                ['NP+AdverbPhrase', 'AdverbPhrase', 'NP+AdverbPhrase', 0.2],

                ['PrepPhrase', 'PrepPhrase', 'NP', 0.1],
                ['PrepPhrase', 'Preposition', 'Name', 0.2],
                ['PrepPhrase', 'Preposition', 'CityName', 0.2],
                ['PrepPhrase', 'Preposition', 'Noun', 0.05],
                ['PrepPhrase', 'Preposition', '', 0.1],

                ['AdverbPhrase', 'PrepPhrase', 'Adverb', 0.3],
                ['AdverbPhrase', 'Adverb', 'PrepPhrase', 0.3],
                ['AdverbPhrase', 'Adverb', 'AdverbPhrase', 0.1],
                ['AdverbPhrase', 'AdverbPhrase', 'Adverb', 0.1],
                ['AdverbPhrase', 'Adverb', '', 0.2],

            ],
            'lexicon' : [
                ['WQuestion', 'what', 0.1],
                ['WQuestion', 'when', 0.2],
                ['WQuestion', 'where', 0.2],
                ['WQuestion', 'which', 0.09],
                ['WQuestion', 'will', 0.01],
                ['WQuestion', 'could', 0.05],
                ['WQuestion', 'should', 0.1],
                ['WQuestion', 'how', 0.1],
                ['WQuestion', 'is', 0.1],

                ['AuxVerb', 'will', 0.33],
                ['AuxVerb', 'to', 0.33],
                ['AuxVerb', 'be', 0.33],

                ['Verb', 'is', 0.2],
                ['Verb', 'be', 0.1],
                ['Verb', 'go', 0.1],
                ['Verb', 'do', 0.1],
                ['Verb', 'want', 0.1],
                ['Verb', 'like', 0.1],

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

                ['Verb', 'rain', 0.02],
                ['Verb', 'snow', 0.02],

                ['Adverb', 'now', 0.15],
                ['Adverb', 'today', 0.15],
                ['Adverb', 'tomorrow', 0.3],
                ['Adverb', 'scuba', 0.1],

                ['Pronoun', 'I', 0.6],
                ['Pronoun', 'we', 0.2],
                ['Pronoun', 'it', 0.2],
                ['Noun', 'temperature', 0.2],
                ['Noun', 'weather', 0.3],
                ['Noun', 'activity', 0.1],
                ['Noun', 'today', 0.05],
                ['Noun', 'tomorrow', 0.05],

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
                ['Det', 'next', 0.5],
                ['Det', 'this', 0.5],

                ['Preposition', 'with', 0.25],
                ['Preposition', 'in', 0.25],
                ['Preposition', 'than', 0.25],
                ['Article', 'the', 0.7],
                ['Article', 'a', 0.3],
                ['Adjective', 'my', 0.2],
                ['Adjective', 'scuba', 0.1],
                ['Adjective', 'hotter', 0.1],
                ['Adjective', 'colder', 0.1],
                ['Adjective', 'warmer', 0.1],
                ['Adjective', 'cooler', 0.1],

                # weather adjectives
                ['Adjective', 'sunny', 0.1],
                ['Adjective', 'raining', 0.1],
                ['Adjective', 'cloudy', 0.1],
                ['Adjective', 'clear', 0.1],
                ['Adjective', 'snowing', 0.1],

                ['S', 'hi', 0.25],
                ['S', 'hello', 0.25],
                ['S', 'hey', 0.25],
                ['S', 'yo', 0.25],
                ['S', 'goodbye', 0.33],
                ['S', 'bye', 0.33],
                ['S', 'bye-bye', 0.33],
            ]
        }

        # adding cities to lexicon
        for city in self.CITY_NAMES:
            self.addLexicon(city, "Name")
        for i in self.CITY_PREFIXES:
            self.addLexicon(i, "CityPrefix")
        for j in self.CITY_SUFFIXES:
            self.addLexicon(j, "CitySuffix")

    def printV(self, *args):
        """For debugging"""
        if self.verbose:
            print(*args)

    def CYKParse(self, words: List[str], grammar):
        """
        A Python implementation of the CYK-Parse algorithm.
        From Artificial Intelligence: A Modern Approach (Russell, Norvig)
        """
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


    def subspans(self, N: int):
        """
        CS 171, Prof. Robert Frost
        Python uses 0-based indexing, requiring some changes from the book's
        1-based indexing: i starts at 0 instead of 1
        """
        for length in range(2, N+1):
            for i in range(N+1 - length):
                k = i + length - 1
                for j in range(i, k):
                    yield i, j, k

    def getGrammarLexicalRules(self, grammar, word: str):
        """
        CS 171, Prof. Robert Frost
        These two getXXX functions use yield instead of return so that a single pair can be sent back,
        and since that pair is a tuple, Python permits a friendly 'X, p' syntax
        in the calling routine.
        """
        for rule in grammar['lexicon']:
            if rule[1].lower() == word.lower():
                yield rule[0], rule[2]

    def getGrammarSyntaxRules(self, grammar):
        for rule in grammar['syntax']:
            yield rule[0], rule[1], rule[2], rule[3]

    def getGrammarWeather(self):
        return self.weatherGrammar

    def setVerbose(self, val: bool):
        self.verbose = val

    def addLexicon(self, city: str, pos: str):
        """
        There is space for 100 cities, so each city is assigned a probability of 0.01.
        All cities are in California only.
        """
        self.weatherGrammar["lexicon"].append(
            [pos, city, 0.01]
        )


# Unit testing code
if __name__ == '__main__':
    c = VacationParser()
    c.setVerbose(True)

    c.CYKParse("is tomorrow hotter".split(), c.getGrammarWeather())




# Hi, I am Peter. I am Peter. Hi, my name is Peter. My name is Peter.
# What is the temperature in Irvine? What is the temperature in Irvine now?
# What is the temperature in Irvine tomorrow?
