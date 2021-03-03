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
        "los angeles", "san francisco", "san diego", "long beach", "santa barbara",
        "torrance", "oceanside", "carlsbad", "newport beach", "huntington beach",
        "santa monica", "oxnard", "ventura"
    }

    ACTIVITIES = {
        "surf", "sail", "fish", "dive", "golf",
        "surfing", "sailing", "fishing", "diving", "golfing"
    }

    WARM_ACTIVITIES = {

    }

    COASTAL_ACTIVITIES = {
        "surf", "sail", "fish", "dive",
        "surfing", "sailing", "fishing", "diving"
    }

    # Activities which may be dangerous if done in not clear/sunny weather
    CLEAR_ACTIVITIES = {
        "hike", "skydive", "kayak", "surf",
        "hiking", "skydiving", "kayaking", "surfing"
    }

    # Activities that can only be done if snowing (which is a bit pointless in California)
    SNOW_ACTIVITIES = {
        "ski", "sled", "snowboard",
        "skiing", "sledding", "snowboarding"
    }

    ALL_ACTIVITIES = ACTIVITIES | CLEAR_ACTIVITIES | SNOW_ACTIVITIES | COASTAL_ACTIVITIES

    WEATHER_KEYWORDS = {
        "raining", "cloudy", "sunny", "snowing", "clear"
    }

    WEATHER_ADJS = {
        "clouds": "cloudy",
        "rain": "raining",
        "clear": "sunny",
        "snow": "snowing"
    }

    # associates the chatbot with instances of CYKParser and OWMWrapper objects
    def __init__(self, parser, wrapper, DEBUG=False):
        self.DEBUG = DEBUG
        self.requestInfo = {
            'time': 'now',
            'location': '',
            'locPrefix': '',
            'locSuffix': '',
            'time0': '',
            'compare': None,    # bool result of comparison
            'compareWord': '',  # hotter/warmer/colder/cooler
            'weatherWord': '',
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
        self.hasWeatherWord = False
        self.isGreeting = False
        self.goodbye = False


    # Given the collection of parse trees returned by CYKParse, this function
    # sets self.sentenceTree as the one corresponding to the complete sentence.
    # If it does not exist, self.sentenceTree is set to None.
    def getSentenceParse(self, T):
        sentenceTrees = {k: v for k, v in T.items() if k.startswith('S/0')}
        if sentenceTrees.keys():
            self.validSentence = True
            completeTree = max(sentenceTrees.keys())
            self.sentenceTree = T[completeTree]
            if self.DEBUG:
                print('getSentenceParse:', self.sentenceTree)
        else:
            self.sentenceTree = None

    # Processes the leaves of the parse tree to pull out the user's request.
    # Resets chatbot state for every user query (except for location and time).
    def updateRequestInfo(self):
        self.comparing = False
        self.hasLocation = False
        self.hasActivity = False
        self.hasTime = False
        self.needsRec = False
        self.question = False
        self.weatherQuery = False
        self.hasWeatherWord = False
        self.isGreeting = False
        self.requestInfo["compare"] = None
        self.requestInfo["time0"] = ""

        if not self.sentenceTree:
            self.validSentence = False
            return

        for leaf in self.sentenceTree.getLeaves():
            if leaf[1] in ("hello", "hi", "hey", "yo"):
                self.isGreeting = True

            if leaf[1] in ("goodbye", "bye-bye", "bye"):
                self.goodbye = True

            if leaf[1] in self.ALL_ACTIVITIES:
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
                if leaf[1] in ("weather", "temperature"):
                    self.weatherQuery = True
                elif leaf[1] in self.WEATHER_KEYWORDS:
                    self.weatherQuery = True
                    self.hasWeatherWord = True
                    self.requestInfo["weatherWord"] = leaf[1]

                if ((leaf[0] == "Verb" and leaf[1] in ("go", "do") and not self.hasActivity) or
                        (leaf[0] == "Verb" and leaf[1] in self.ALL_ACTIVITIES)):
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

            if self.DEBUG:
                print(self.sentenceTree)
                print("self.validSentence:", self.validSentence)
                print("self.comparing:", self.comparing)
                print("self.hasLocation:", self.hasLocation)
                print("self.hasActivity:", self.hasActivity)
                print("self.hasTime:", self.hasTime)
                print("self.needsRec:", self.needsRec)
                print("self.question:", self.question)
                print("self.weatherQuery:", self.weatherQuery)
                print("self.hasWeatherWord:", self.hasWeatherWord)
                print("self.isGreeting:", self.isGreeting)
                print("self.goodbye:", self.goodbye)
                print("updateRequestInfo", self.requestInfo)

    # gives user input to chatbot
    def say(self, sentence):
        self.sentenceTree, _ = self.Parser.CYKParse(sentence.lower().split(), self.Parser.getGrammarWeather())
        self.getSentenceParse(self.sentenceTree)
        self.updateRequestInfo()

    # Format a reply to the user, based on what the user wrote.
    def reply(self):
        if self.DEBUG:
            print("replying")
        if self.validSentence:
            if self.isGreeting:
                greeting_templates = (
                    "How can I help?",
                    "What can I do for you?",
                    "Hello!",
                    "Hi! I can help you with anything vacation related!"
                )
                print(random.choice(greeting_templates))

            if self.goodbye:
                bye_templates = (
                    "Have a nice trip, and stay safe.",
                    "Bye-bye! Have a great vacation.",
                    "Goodbye! I hope my recommendations helped you out.",
                    "See you next time!"
                )
                print(random.choice(bye_templates))

            elif self.weatherQuery:
                if self.requestInfo["location"] or (self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]):
                    loc = ""
                    if self.requestInfo["location"]:
                        loc = self.formatCityName(
                            self.requestInfo["location"]
                        )
                    elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                        loc = self.formatCityName(
                            f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                        )

                    time = self.requestInfo["time"]
                    temp = self.getTemperature(loc, time)
                    weather = self.weatherAdj(
                                    self.getWeather(loc, time)
                                )
                    if self.hasWeatherWord:
                        w = self.weatherAdj(
                                self.requestInfo["weatherWord"]
                            )
                        if weather == w:
                            print(f"Yes, it's {weather} in {loc} {time}.")
                        else:
                            print(f"No, it's not {weather} in {loc} {time}.")
                    else:
                        templates = (
                            f"The weather in {loc} {time} is {weather}, with a temperature of {temp}F.",
                            f"It's {weather} {time} in {loc}, with a temperature of {temp}F."
                        )
                        print(random.choice(templates))

            elif self.needsRec:
                if ((not self.requestInfo["location"] or
                        (self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]))
                        and not self.requestInfo["time"]):
                    pass

                elif (not self.requestInfo["location"] or
                        (self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"])):
                    pass

                elif not self.requestInfo["time"]:
                    pass

                else:
                    loc = ""
                    if self.requestInfo["location"]:
                        loc = self.formatCityName(
                            self.requestInfo["location"]
                        )
                    elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                        loc = self.formatCityName(
                            f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                        )

                    time = self.requestInfo["time"]


            elif self.comparing:
                if self.requestInfo["location"]:
                    loc = self.formatCityName(
                        self.requestInfo["location"]
                    )
                elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                    loc = self.formatCityName(
                        f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                    )

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
            elif self.needsRec:
                pass

        else:
            invalid_templates = (
                "Remember, I only talk about weather and vacations, so I'm not very good with other topics.",
                "Sorry, I didn't understand what you said. Can you rephrase that again?",
                "Can you rephrase that again? I didn't understand that sentence.",
                "I hope that's a real sentence, because I didn't understand any of that.",
                "You'll have to excuse my very small vocabulary, "
                "so let's try to talk about weather and vacations."
            )
            print(random.choice(invalid_templates))

    ############### UTILITY FUNCTIONS #########################################
    def getTemperature(self, location, time):
        return self.getCityInfo(location, time)[0]

    def getWeather(self, location, time):
        return self.getCityInfo(location, time)[1]

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
                # REMINDER to check response codes and maybe have the chatbot respond accordingly

            temp = self.Wrapper.getCityTemp(location, t)
            weather = self.Wrapper.getCityWeather(location, t)
            if self.DEBUG:
                print(f"getTemperature {temp} {weather}")

            # getCityTemp returns NaN if couldn't get temperature
            if temp == temp and weather != "unknown":
                return (temp, weather)

        return ("unknown", "unknown")

    # Capitalizes first letter in city names. Ex: san jose -> San Jose, irvine -> Irvine
    def formatCityName(self, city):
        return " ".join([s.capitalize() for s in city.split()])

    # Gets the adjective word of weather. Ex: clouds -> cloudy, clear -> sunny (both are the same)
    def weatherAdj(self, weather):
        if weather in self.WEATHER_ADJS:
            return self.WEATHER_ADJS[weather]
        else:
            return weather


if __name__ == "__main__":
    # T, P = CYKParse.CYKParse(['hi', 'I', 'is', 'Peter'], CYKParse.getGrammarWeather())
    user_in = ""
    c = VacationBot(VacationParser(), OWMWrapper(), True)   # remove third param to disable debugging
    while user_in not in ("goodbye", "bye", "bye-bye"):
        user_in = input("User>")
        c.say(user_in)
        c.reply()

