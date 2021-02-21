from CYKParse import VacationParser
from Weather import OWMQuery

class VacationBot:
    # associates the chatbot with instances of CYKParser and OWMQuery objects
    def __init__(self, parser, query):
        self.requestInfo = {
            'time': 'now',
            'location': '',
            'time0': '',
            'compare': None,
            'compareWord': ''
        }
        self.Parser = parser
        self.Query = query
        self.sentenceTree = None
        self.comparing = False
        self.lookingForLocation = False
        self.lookingForName = False

    # Given the collection of parse trees returned by CYKParse, this function
    # returns the one corresponding to the complete sentence.
    def getSentenceParse(self, T):
        sentenceTrees = {k: v for k, v in T.items() if k.startswith('S/0')}
        completeTree = max(sentenceTrees.keys())
        self.sentenceTree = T[completeTree]
        print('getSentenceParse:', self.sentenceTree)
        return self.sentenceTree

    # Processes the leaves of the parse tree to pull out the user's request.
    def updateRequestInfo(self, Tr):
        self.lookingForLocation = False
        self.lookingForName = False
        time0 = ''

        for leaf in Tr.getLeaves():
            # get temperature in one location
            if leaf[0] == 'Adverb':
                self.requestInfo['time'] = leaf[1]
            if self.lookingForLocation and leaf[0] == 'Name':
                self.requestInfo['location'] = leaf[1]
            self.lookingForLocation = leaf[0] == 'Preposition' and leaf[1] == 'in'

            """
            'Will' will compare two temps from two different times.
            First it gets the first time and save it, then we store the second time in requestInfo, 
            then it gets the location and compare the two temperatures from the times.
            """
            if leaf[0] == 'WQuestion' and leaf[1] == 'will':
                self.comparing = True
                self.requestInfo['time'] = ''
                self.requestInfo['time0'] = ''
                self.requestInfo['location'] = ''
            if self.comparing:
                if not (self.requestInfo['time'] and self.requestInfo['location']):
                    if leaf[0] == 'Adjective':
                        self.requestInfo['compareWord'] = leaf[1]
                    if leaf[0] == 'Adverb' and time0 == '':
                        time0 = leaf[1]
                    elif leaf[0] == 'Adverb' and time0:
                        self.requestInfo['time'] = leaf[1]
                    if self.lookingForLocation and leaf[0] == 'Name':
                        self.requestInfo['location'] = leaf[1]
                else:
                    # compare the two temperatures here
                    self.requestInfo['time0'] = time0
                    # print(requestInfo['location'],
                    #         requestInfo['time0'], getTemperature(requestInfo['location'], requestInfo['time0']),
                    #         requestInfo['time'], getTemperature(requestInfo['location'], requestInfo['time']))

                    if self.requestInfo['compareWord'] in ('hotter', 'warmer'):
                        self.requestInfo['compare'] = \
                            self.getTemperature(self.requestInfo['location'], self.requestInfo['time']) \
                            < self.getTemperature(self.requestInfo['location'], self.requestInfo['time0'])
                    elif self.requestInfo['compareWord'] in ('colder', 'cooler'):
                        self.requestInfo['compare'] = \
                            self.getTemperature(self.requestInfo['location'], self.requestInfo['time']) \
                            > self.getTemperature(self.requestInfo['location'], self.requestInfo['time0'])
            else:
                self.comparing = False

            # print(leaf, 'comparing=', self.comparing, 'loc=', self.lookingForLocation)

    # uses the OWMQuery object to get weather if it doesn't exist in local DB already
    def getTemperature(self, location, time):
        if location.lower() == 'irvine':
            if time == 'now' or time == 'today':
                return '68'
            elif time == 'yesterday':
                return '69'
            elif time == 'tomorrow':
                return '70'
            else:
                return 'unknown'
        elif location.lower() == 'tustin':
            if time == 'now' or time == 'today':
                return '58'
            elif time == 'yesterday':
                return '59'
            elif time == 'tomorrow':
                return '60'
            else:
                return 'unknown'
        elif location.lower() == 'pasadena':
            if time == 'now' or time == 'today':
                return '78'
            elif time == 'yesterday':
                return '79'
            elif time == 'tomorrow':
                return '80'
            else:
                return 'unknown'

        else:
            return 'unknown'

    # Format a reply to the user, based on what the user wrote.
    def reply(self):
        print(self.requestInfo, self.comparing)
        if self.comparing and self.requestInfo['compare'] is not None:
            if self.requestInfo['compare']:
                print("Yes,", self.requestInfo['time0'], 'is', self.requestInfo['compareWord'], 'than',
                      self.requestInfo['time'], 'in', self.requestInfo['location'] + '. ', end='')
            else:
                print("No,", self.requestInfo['time0'], 'is not', self.requestInfo['compareWord'], 'than',
                      self.requestInfo['time'], 'in', self.requestInfo['location'] + '. ', end='')
            print(self.requestInfo['time0'], 'is', self.getTemperature(self.requestInfo['location'], self.requestInfo['time0']),
                  'and', self.requestInfo['time'], 'is', self.getTemperature(self.requestInfo['location'], self.requestInfo['time']))
            return

        if self.requestInfo['time'] != '':
            time = self.requestInfo['time']
        print('the temperature in ' + self.requestInfo['location'] + ' ' + self.requestInfo['time'] +
              ' is ' + self.getTemperature(self.requestInfo['location'], self.requestInfo['time']) + '.')

# requestInfo = {
#         'time': '',
#         'location': '',
#         'time0': '',
#         'compare': None,
#         'compareWord': ''
# }
# haveGreeted = False
# comparing = False
#
# # Given the collection of parse trees returned by CYKParse, this function
# # returns the one corresponding to the complete sentence.
# def getSentenceParse(T):
#     sentenceTrees = { k: v for k,v in T.items() if k.startswith('S/0') }
#     completeSentenceTree = max(sentenceTrees.keys())
#     # print('getSentenceParse', completeSentenceTree)
#     return T[completeSentenceTree]
#
# # Processes the leaves of the parse tree to pull out the user's request.
# def updateRequestInfo(Tr):
#     global requestInfo
#     global comparing
#     lookingForLocation = False
#     lookingForName = False
#     time0 = ''
#
#     for leaf in Tr.getLeaves():
#         # get temperature in one location
#         if leaf[0] == 'Adverb':
#             requestInfo['time'] = leaf[1]
#         if lookingForLocation and leaf[0] == 'Name':
#             requestInfo['location'] = leaf[1]
#         if leaf[0] == 'Preposition' and leaf[1] == 'in':
#             lookingForLocation = True
#         else:
#             lookingForLocation = False
#
#         """
#         'Will' will compare two temps from two different times.
#         First it gets the first time and save it, then we store the second time in requestInfo,
#         then it gets the location and compare the two temperatures from the times.
#         """
#         if leaf[0] == 'WQuestion' and leaf[1] == 'will':
#             comparing = True
#             requestInfo['time'] = ''
#             requestInfo['time0'] = ''
#             requestInfo['location'] = ''
#         if comparing:
#             if not (requestInfo['time'] and requestInfo['location']):
#                 if leaf[0] == 'Adjective':
#                     requestInfo['compareWord'] = leaf[1]
#                 if leaf[0] == 'Adverb' and time0 == '':
#                     time0 = leaf[1]
#                 elif leaf[0] == 'Adverb' and time0:
#                     requestInfo['time'] = leaf[1]
#                 if lookingForLocation and leaf[0] == 'Name':
#                     requestInfo['location'] = leaf[1]
#             else:
#                 # compare the two temperatures here
#                 requestInfo['time0'] = time0
#                 # print(requestInfo['location'],
#                 #         requestInfo['time0'], getTemperature(requestInfo['location'], requestInfo['time0']),
#                 #         requestInfo['time'], getTemperature(requestInfo['location'], requestInfo['time']))
#
#                 if requestInfo['compareWord'] == 'hotter':
#                     requestInfo['compare'] = getTemperature(requestInfo['location'], requestInfo['time']) \
#                                             < getTemperature(requestInfo['location'], requestInfo['time0'])
#                 elif requestInfo['compareWord'] == 'colder':
#                     requestInfo['compare'] = getTemperature(requestInfo['location'], requestInfo['time']) \
#                                              > getTemperature(requestInfo['location'], requestInfo['time0'])
#         else:
#             comparing = False
#
#
#         # get name section
#         if leaf[0] == 'Noun' and leaf[1] == 'name' or leaf[0] == 'Pronoun' and leaf[1] == 'I':
#             lookingForName = True
#         if lookingForName and leaf[0] == 'Name':
#             requestInfo['name'] = leaf[1]
#
#         # print(leaf, 'comparing=', comparing, 'loc=', lookingForLocation, 'name=', lookingForName)
#
#
# # This function contains the data known by our simple chatbot
# def getTemperature(location, time):
#     if location == 'Irvine':
#         if time == 'now' or time == 'today':
#             return '68'
#         elif time == 'yesterday':
#             return '69'
#         elif time == 'tomorrow':
#             return '70'
#         else:
#             return 'unknown'
#     elif location == 'Tustin':
#         if time == 'now' or time == 'today':
#             return '58'
#         elif time == 'yesterday':
#             return '59'
#         elif time == 'tomorrow':
#             return '60'
#         else:
#             return 'unknown'
#     elif location == 'Pasadena':
#         if time == 'now' or time == 'today':
#             return '78'
#         elif time == 'yesterday':
#             return '79'
#         elif time == 'tomorrow':
#             return '80'
#         else:
#             return 'unknown'
#
#     else:
#         return 'unknown'
#
# # Format a reply to the user, based on what the user wrote.
# def reply():
#     global requestInfo
#     global haveGreeted
#     global comparing
#     if not haveGreeted and requestInfo['name'] != '':
#         print("Hello", requestInfo['name'] + '.')
#         haveGreeted = True
#         return
#
#     if comparing and requestInfo['compare'] is not None:
#         if requestInfo['compare']:
#             print("Yes,", requestInfo['time0'], 'is', requestInfo['compareWord'], 'than',
#                   requestInfo['time'], 'in', requestInfo['location'] + '. ', end='')
#         else:
#             print("No,", requestInfo['time0'], 'is not', requestInfo['compareWord'], 'than',
#                   requestInfo['time'], 'in', requestInfo['location'] + '. ', end='')
#         print(requestInfo['time0'], 'is', getTemperature(requestInfo['location'], requestInfo['time0']),
#               'and', requestInfo['time'], 'is', getTemperature(requestInfo['location'], requestInfo['time']))
#         return
#
#     time = 'now' # the default
#     if requestInfo['time'] != '':
#         time = requestInfo['time']
#     salutation = ''
#     if requestInfo['name'] != '':
#         salutation = requestInfo['name'] + ', '
#     print(salutation + 'the temperature in ' + requestInfo['location'] + ' ' +
#         time + ' is ' + getTemperature(requestInfo['location'], time) + '.')


if __name__ == "__main__":
    # T, P = CYKParse.CYKParse(['hi', 'I', 'is', 'Peter'], CYKParse.getGrammarWeather())
    user_in = ""
    while user_in != "exit":
        user_in = input("User>")
        c = VacationBot(VacationParser(), OWMQuery())
        T, P = c.Parser.CYKParse("what is the temperature tomorrow in Irvine".split(), c.Parser.getGrammarWeather())
        print(c.sentenceTree)
        c.updateRequestInfo(c.getSentenceParse(T))
        c.reply()

    # # T, P = CYKParse.CYKParse(['hi', 'I', 'is', 'Peter'], CYKParse.getGrammarWeather())
    # T, P = CYKParse.CYKParse(['hi', 'my', 'name', 'is', 'Peter'], CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()

    # T, P = CYKParse.CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'now'], CYKParse.getGrammarWeather())
    # T, P = CYKParse.CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'tomorrow'], CYKParse.getGrammarWeather())
    # T, P = CYKParse.CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Tustin', 'yesterday'], CYKParse.getGrammarWeather())
    # T, P = CYKParse.CYKParse("will tomorrow be hotter than today in Irvine".split(), CYKParse.getGrammarWeather())

    # T, P = CYKParse.CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Tustin', 'yesterday'], CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()

    # T, P = CYKParse.CYKParse(['what', 'is', 'now', 'the', 'temperature', 'in', 'Irvine'], CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()
    #
    # T, P = CYKParse.CYKParse(['what', 'is', 'the', 'temperature', 'in', 'Irvine', 'tomorrow'], CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()
    #
    # T, P = CYKParse.CYKParse("will today be colder than tomorrow in Pasadena".split(), CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()
    #
    # T, P = CYKParse.CYKParse("will today be hotter than today in".split(), CYKParse.getGrammarWeather())
    # sentenceTree = getSentenceParse(T)
    # updateRequestInfo(sentenceTree)
    # reply()
