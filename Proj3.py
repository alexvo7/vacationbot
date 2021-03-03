from CYKParse import VacationParser
from Weather import OWMWrapper
import random

class VacationBot:
    HOTSPOTS = {
        "Los Angeles", "San Francisco", "San Diego", "Santa Monica", "Santa Barbara",
        "Santa Cruz", "Long Beach", "Sacramento", "Anaheim", "Oakland",
        "Berkeley", "San Jose"
    }

    COASTAL_CITIES = {
        # to be added in part 4
    }

    ACTIVITIES = {
        "surf", "sail",
        "kayak", "fish", "dive", "golf",
        "surfing", "sailing",
        "kayaking", "fishing", "diving", "golfing",
    }

    # Activities which may be dangerous if done in not clear/sunny weather
    CLEAR_ACTIVITIES = {
        "hike", "skydive",
        "hiking", "skydiving"
    }

    # Activities that can only be done if snowing (which is a bit pointless in California)
    SNOW_ACTIVITIES = {
        "ski", "sled", "snowboard",
        "skiing", "sledding", "snowboarding",
    }

    WEATHER_KEYWORDS = {
        "rainy", "cloudy", "sunny", "snowy", "clear"
    }

    # associates the chatbot with instances of CYKParser and OWMWrapper objects
    def __init__(self, parser, wrapper):
        self.requestInfo = {
            'time': 'now',
            'location': '',
            'locPrefix': '',
            'locSuffix': '',
            'time0': '',
            'compare': None,    # bool result of comparison
            'compareWord': '',  # hotter/warmer/colder/cooler
            'activity': '',

        }

        self.Parser = parser
        self.Wrapper = wrapper
        self.sentenceTree = None
        self.validSentence = False

        # chatbot state flags
        self.comparing = False
        self.hasLocation = False
        self.hasActivity = False
        self.hasTime = False
        self.needsRec = False
        self.question = False
        self.weatherQuery = False
        self.goodbye = False

    # Given the collection of parse trees returned by CYKParse, this function
    # returns the one corresponding to the complete sentence.
    def getSentenceParse(self, T):
        sentenceTrees = {k: v for k, v in T.items() if k.startswith('S/0')}
        if sentenceTrees.keys():
            self.validSentence = True
            completeTree = max(sentenceTrees.keys())
            self.sentenceTree = T[completeTree]
            print('getSentenceParse:', self.sentenceTree)
            return self.sentenceTree
        else:
            return None

    # Processes the leaves of the parse tree to pull out the user's request.
    def updateRequestInfo(self):
        self.comparing = False
        self.hasLocation = False
        self.hasActivity = False
        self.hasTime = False
        self.needsRec = False
        self.question = False
        self.weatherQuery = False
        self.requestInfo["compare"] = None
        self.requestInfo["time0"] = ""

        for leaf in self.sentenceTree.getLeaves():
            if leaf[1] in ("goodbye", "bye-bye", "bye"):
                self.goodbye = True

            if leaf[1] in self.ACTIVITIES:
                self.requestInfo["activity"] = leaf[1]
                self.hasActivity = True

            if leaf[0] == "WQuestion":
                self.question = True

            if leaf[0] == 'Adverb' and not self.hasTime:
                self.requestInfo['time'] = leaf[1]
                self.hasTime = True

            if not self.hasLocation and leaf[0] in ("Name", "CityPrefix", "CitySuffix"):
                if leaf[0] == "Name":
                    self.requestInfo["location"] = leaf[1]
                    self.requestInfo["locPrefix"] = ""
                    self.requestInfo["locSuffix"] = ""
                    self.hasLocation = True
                else:
                    self.requestInfo["location"] = ""
                    if leaf[0] == "CityPrefix":
                        self.requestInfo["locPrefix"] = leaf[1]
                    else:
                        self.requestInfo["locSuffix"] = leaf[1]
                        self.hasLocation = True

            if self.question:
                if leaf[1] in self.WEATHER_KEYWORDS or leaf[1] in ("weather", "temperature"):
                    self.weatherQuery = True
                if leaf[0] == "Verb" and leaf[1] in ("go", "do") and not self.hasActivity:
                    self.needsRec = True

            if self.hasActivity and leaf[0] == "Verb" and leaf[1] == "want":
                self.needsRec = True

            if leaf[0] == "Preposition" and leaf[1] == "than":
                self.comparing = True

            if leaf[0] == "Adjective" and leaf[1] in ("hotter", "warmer", "cooler", "colder"):
                self.requestInfo["compareWord"] = leaf[1]

            if self.comparing:
                if not self.requestInfo["time0"] and leaf[1] in ("today", "tomorrow"):
                    time0 = self.requestInfo["time0"] = leaf[1]

                if self.hasLocation:
                    time0 = self.requestInfo["time0"]
                    time = self.requestInfo["time"]
                    loc = ""
                    if self.requestInfo["location"]:
                        loc = self.requestInfo["location"]
                    elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                        loc = f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"

                    time0_temp = self.getTemperature(loc, time0)
                    time_temp = self.getTemperature(loc, time)

                    if (time0_temp != "unknown" and time_temp != "unknown"):
                        if self.requestInfo['compareWord'] in ('hotter', 'warmer'):
                            self.requestInfo['compare'] = time_temp > time0_temp
                        elif self.requestInfo['compareWord'] in ('colder', 'cooler'):
                            self.requestInfo['compare'] = time_temp < time0_temp

        print(f"updateRequestInfo {self.requestInfo}")
        print("self.comparing:",self.comparing)
        print("self.hasLocation:",self.hasLocation)
        print("self.hasActivity:",self.hasActivity)
        print("self.hasTime:",self.hasTime)
        print("self.needsRec:",self.needsRec)
        print("self.question:",self.question)
        print("self.weatherQuery:",self.weatherQuery)

    # Uses the OWMWrapper object to get weather if it doesn't exist in local DB already.
    # Returns "unknown" if location/temp doesn't exist.
    # We can't handle "week" here since this function only returns one value
    # Strangely, "this week" and "next week" get the same thing since we can only
    # get a 7 day forecast anyway.
    def getCityInfo(self, location, time):
        location = location.lower()
        time = time.lower()
        t = 0
        if time == "tomorrow":
            t = 1
        if time in ("now", "today", "tomorrow"):
            if not (location in self.Wrapper.DB and t in self.Wrapper.DB[location]):
                if time == "tomorrow":
                    self.Wrapper.getWeekly(location)
                else:
                    self.Wrapper.get(location)

            temp = self.Wrapper.getCityTemp(location, t)
            weather = self.Wrapper.getCityWeather(location, t)
            print(f"getTemperature {temp} {weather}")
            # getCityTemp returns NaN if couldn't get temperature
            if temp == temp and weather != "unknown":
                return (temp, weather)
        return ("unknown", "unknown")

    def getTemperature(self, location, time):
        return self.getCityInfo(location, time)[0]

    def getWeather(self, location, time):
        return self.getCityInfo(location, time)[1]

    # gives user input to chatbot
    def userSay(self, sentence):
        self.sentenceTree, _ = self.Parser.CYKParse(sentence.lower().split(), self.Parser.getGrammarWeather())
        self.sentenceTree = self.getSentenceParse(self.sentenceTree)
        if self.sentenceTree:
            self.updateRequestInfo()

    # Format a reply to the user, based on what the user wrote.
    def reply(self):
        if self.validSentence:
            if self.goodbye:
                bye_templates = (
                    "Have a nice trip, and stay safe.",
                    "Goodbye, and have a great vacation.",
                    "Bye-bye! I hope my recommendations helped you out.",
                    "See you next time."
                )
                print(random.choice(bye_templates))

            elif self.weatherQuery:
                if self.requestInfo["location"] or (self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]):
                    if self.requestInfo["location"]:
                        loc = self.requestInfo["location"]
                    elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                        loc = f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                    time = self.requestInfo["time"]
                    temp = self.getTemperature(loc, time)
                    weather = self.getWeather(loc, time)

                    templates = (
                        f"The weather in {loc} {time} is {weather}, with a temperature of {temp}F.",
                        f"It's {weather} {time} in {loc}, with a temperature of {temp}F."
                    )
                    print(random.choice(templates))

            elif self.comparing:
                if self.requestInfo["location"]:
                    loc = self.requestInfo["location"]
                elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                    loc = f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                time = self.requestInfo["time"]
                time0 = self.requestInfo["time0"]
                temp = self.getTemperature(loc, time)
                temp0 = self.getTemperature(loc, time0)
                comp = self.requestInfo["compareWord"]
                if self.requestInfo["compare"]:
                    print(f"Yes, {time} is {comp} than {time0} in {loc}. "
                          f"It is {temp}F {time} and {temp0}F {time0}.")
                else:
                    print(f"No, {time} is not {comp} than {time0} in {loc}. "
                          f"It is {temp}F {time} and {temp0}F {time0}.")
        else:
            invalid_templates = (
                "Remember that I only talk about weather and vacations, and I don't do well with other topics.",
                "Sorry, I didn't understand what you said. Can you rephrase that again?",
                "Can you rephrase that again? I didn't understand that sentence.",
                "You'll have to excuse my very small vocabulary, "
                "so please try to keep it relevant to weather and vacations and that kind of stuff."
            )
            print(random.choice(invalid_templates))



if __name__ == "__main__":
    # T, P = CYKParse.CYKParse(['hi', 'I', 'is', 'Peter'], CYKParse.getGrammarWeather())
    user_in = ""
    c = VacationBot(VacationParser(), OWMWrapper())
    while user_in not in ("goodbye", "bye", "bye-bye"):
        user_in = input("User>")
        c.userSay(user_in)
        c.reply()

