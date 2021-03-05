from CYKParse import VacationParser, Tree
from Weather import OWMWrapper
from typing import List
import random


class VacationBot:
    VALID_CITIES = {
        "santa": {"ana", "clarita", "rosa", "clara", "barbara", "monica", "maria"},
        "san": {"jose", "francisco", "diego", "bernardino", "mateo", "marcos", "leandro"},
        "newport": ["beach"],
        "west": ["covina"],
        "long": ["beach"],
        "daly": ["city"],
        "mission": ["viejo"],
        "costa": ["mesa"],
        "elk": ["grove"],
        "redwood": ["city"],
        "citrus": ["heights"],
        "rancho": ["cucamonga"],
        "lake": ["forest"],
        "chula": ["vista"],
        "simi": ["valley"],
        "jurupa": ["valley"],
        "moreno": ["valley"],
        "thousand": ["oaks"],
        "huntington": ["beach"],
        "south": ["gate"],
        "garden": ["grove"],
        "los": ["angeles"],
        "chino": ["hills"],
        "el": ["monte", "cajon"]
    }

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

    COASTAL_ACTIVITIES = {
        "surf", "sail", "fish", "dive",
        "surfing", "sailing", "fishing", "diving"
    }

    # Activities which may be dangerous/not ideal in not clear/sunny weather
    CLEAR_ACTIVITIES = {
        "hike", "skydive", "kayak", "surf", "golf", "fish",
        "hiking", "skydiving", "kayaking", "surfing", "golfing", "fishing"
    }

    # Activities that can only be done if snowing (which is a bit pointless in California)
    SNOW_ACTIVITIES = {
        "ski", "sled", "snowboard",
        "skiing", "sledding", "snowboarding"
    }

    ALL_ACTIVITIES = CLEAR_ACTIVITIES | SNOW_ACTIVITIES | COASTAL_ACTIVITIES

    WEATHER_KEYWORDS = {
        "raining", "cloudy", "sunny", "snowing", "clear", "rain", "snow"
    }

    WEATHER_ADJS = {
        "clouds": "cloudy",
        "rain": "raining",
        "clear": "sunny",
        "snow": "snowing"
    }

    def __init__(self, parser: VacationParser, wrapper: OWMWrapper, DEBUG=False):
        """Associates the chatbot with instances of CYKParser and OWMWrapper objects."""
        self.DEBUG = DEBUG
        self.requestInfo = {
            'time': 'now',
            'location': '',
            'locPrefix': '',
            'locSuffix': '',
            'time0': '',        # used when comparing
            'compareWord': '',  # hotter/warmer/colder/cooler
            'weatherWord': '',
            'activity': ''
        }

        self.Parser = parser
        self.Wrapper = wrapper
        self.sentenceTree = None
        self.tokens = -1

        # chatbot state flags
        self.validSentence = False
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
        self.invalidLocation = False

    def getSentenceParse(self, T: Tree):
        """
        Given the collection of parse trees returned by CYKParse, this function
        sets self.sentenceTree as the one corresponding to the complete sentence.
        If it does not exist, self.sentenceTree is set to None.
        A sentence is valid if all tokens in user input are parsed.
        """
        sentenceTrees = {k: v for k, v in T.items() if k.startswith('S/0')}
        if sentenceTrees.keys():
            completeTree = max(sentenceTrees.keys())    # completeTree formatted "S/0/#"
            if int(completeTree[-1]) + 1 != self.tokens:
                self.sentenceTree = None
                return
            self.validSentence = True
            self.sentenceTree = T[completeTree]
            if self.DEBUG:
                print('getSentenceParse:', self.sentenceTree)
        else:
            self.sentenceTree = None


    def updateRequestInfo(self):
        """
        Processes the leaves of the parse tree to pull out the user's request.
        Resets chatbot state for every user query (except for location and time).
        """
        self.resetStatus()

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

            if leaf[1] in ("today", "tomorrow") and not self.hasTime:
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
                    elif leaf[0] == "CitySuffix":
                        self.requestInfo["locSuffix"] = leaf[1]
                        self.hasLocation = True
                        if leaf[1] not in self.VALID_CITIES[self.requestInfo["locPrefix"]]:
                            self.hasLocation = False
                            self.invalidLocation = True
                    else:
                        self.requestInfo["locPrefix"] = ""
                        self.requestInfo["locSuffix"] = ""
                        self.hasLocation = False
                        self.invalidLocation = True

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
                    loc = self.getLocation()

                    time0_temp = self.getTemperature(loc, time0)
                    time_temp = self.getTemperature(loc, time)

    def say(self, sentence: str):
        """Gives user input to chatbot."""
        if self.DEBUG and sentence == "print":
            print("PRINT DEBUG")
            print("\tself.requestInfo: ", self.requestInfo)
            print("\tself.Wrapper.DB: ", self.Wrapper.DB)
            self.resetStatus()
            return
        elif not self.DEBUG and sentence == "print":
            print("\"print\" is not available if self.DEBUG = False.")

        tokens = sentence.lower().split()
        self.tokens = len(tokens)
        self.sentenceTree, _ = self.Parser.CYKParse(tokens, self.Parser.getGrammarWeather())
        self.getSentenceParse(self.sentenceTree)
        self.updateRequestInfo()


    def reply(self):
        """Format a reply to the user, based on what the user wrote."""
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
            print("self.invalidLocation:", self.invalidLocation)
            print("self.requestInfo:", self.requestInfo)

        if self.DEBUG and self.validSentence:
            print("REPLYING")
        if self.validSentence:
            if self.isGreeting:
                greeting_templates = [
                    "How can I help?",
                    "What can I do for you?",
                    "Hello!",
                    "Hi! I can help you with anything vacation related!"
                ]
                print(random.choice(greeting_templates))
                return

            if self.goodbye:
                bye_templates = [
                    "Have a nice trip, and stay safe.",
                    "Bye-bye! Have a great vacation.",
                    "Goodbye! I hope my recommendations helped you out.",
                    "See you next time!"
                ]
                print(random.choice(bye_templates))
                return

            if self.invalidLocation and self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
                loc = self.formatCityName(
                    f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
                )
                print(f"{loc} is an invalid location for me. Sorry, I can't help you with that.")
                return

            elif self.weatherQuery:
                if not self.hasLocation and not self.hasTime:
                    city1, city2 = tuple(random.sample(tuple(self.HOTSPOTS), 2))
                    city1, city2 = self.formatCityName(city1), self.formatCityName(city2)
                    print(f"I need a place and a time. Today in {city1}? Tomorrow in {city2}?")
                elif not self.hasLocation:
                    w = self.weatherAdj(
                        self.requestInfo["weatherWord"]
                    )
                    time = self.requestInfo["time"]
                    print(f"Will it be {w} {time} where?")
                elif not self.hasTime:
                    loc = self.formatCityName(
                        self.getLocation()
                    )
                    print(f"I can get the weather in {loc}, but I need the time. Today? Tomorrow?")
                else:
                    loc = self.formatCityName(
                        self.getLocation()
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
                            print(f"Yes, it's {w} in {loc} {time}.")
                        else:
                            print(f"No, it's not {w} in {loc} {time}. It's {weather}.")
                    else:
                        templates = [
                            f"The weather in {loc} {time} is {weather}, with a temperature of {temp}F.",
                            f"It's {weather} {time} in {loc}, with a temperature of {temp}F."
                        ]
                        print(random.choice(templates))

            elif self.needsRec:
                if not (self.hasLocation or self.hasActivity):
                    suggestions = self.citySuggestions(self.HOTSPOTS)
                    loc_rec_template = [
                        f"{suggestions} are all great cities to visit!",
                        f"There are some great things to do in {suggestions}!",
                        f"{suggestions} are some of the most popular locations in California. "
                        f"You should check them out!"
                    ]
                    print(random.choice(loc_rec_template))

                elif not self.hasLocation:
                    activity = self.requestInfo["activity"]
                    if activity in self.COASTAL_ACTIVITIES:
                        suggestions = self.citySuggestions(self.COASTAL_CITIES)
                        loc_prog_template = [
                            f"{suggestions} are nice cities for {activity}!",
                            f"I think {suggestions} are great places for {activity}.",
                            f"{activity.capitalize()}? {suggestions} are some good places."
                        ]
                        loc_template = [
                            f"{suggestions} are nice cities to {activity} in!",
                            f"I think {suggestions} are great places to {activity}.",
                            f"You want to {activity}? {suggestions} are some good places."
                        ]
                        print(f"Depends on the weather. "
                              f"{self.recommendStr(activity, loc_prog_template, loc_template)}")

                    elif activity in self.CLEAR_ACTIVITIES:
                        suggestions = self.citySuggestions(self.HOTSPOTS)
                        loc_prog_template = [
                            f"{suggestions} are nice cities for {activity}!",
                            f"I think {suggestions} are great places for {activity}.",
                            f"{activity.capitalize()}? {suggestions} are some good places."
                        ]
                        loc_template = [
                            f"{suggestions} are nice cities to {activity} in!",
                            f"I think {suggestions} are great places to {activity}.",
                            f"You want to {activity}? {suggestions} are some good places."
                        ]
                        print(f"Depends on the weather. "
                              f"{self.recommendStr(activity, loc_prog_template, loc_template)}")

                    elif activity in self.SNOW_ACTIVITIES:
                        print(f"Snow is pretty rare here, but if you want to go {activity}, check the weather first!")

                    else:
                        # The code should NOT reach here
                        print("Something went wrong... your sentence may have been worded funny.")

                elif not self.hasActivity:
                    loc = self.formatCityName(
                        self.getLocation()
                    )

                    if loc in self.COASTAL_CITIES:
                        print(f"Since {loc} is a coastal city, you can take the opportunity to "
                              f"go surfing, sailing, or scuba diving! Or you can do regular activities "
                              f"such as hiking and golfing.")
                    else:
                        print(f"Depending on the weather, you can go "
                              f"{random.choice(tuple(self.CLEAR_ACTIVITIES))} in {loc}.")

                else:
                    loc = self.formatCityName(
                        self.getLocation()
                    )

                    time = self.requestInfo["time"]
                    temp = self.getTemperature(loc, time)
                    wind = self.getWind(loc, time)
                    activity = self.requestInfo["activity"]
                    good_template = [
                        f"Yes, {loc} is a great place to go {activity} {time}.",
                        f"You should definitely go {activity} there. Great choice!",
                        f"I see nothing wrong with that. Enjoy your trip!"
                    ]

                    if temp != "unknown" and float(temp) < 50:
                        print(f"The temperature is {temp}F, which is too cold for "
                              f"most activities (except snowy ones).")
                    else:
                        # arbitrary number, but 20 mph wind must be uncomfortable, so no vacation
                        if wind != "unknown" and float(wind) < 20:
                            weather = self.weatherAdj(self.getWeather(loc, time))

                            if (activity in self.COASTAL_ACTIVITIES
                                    and loc.lower() in self.COASTAL_CITIES
                                    and weather not in ("raining", "snowing")):
                                print(random.choice(good_template))
                                return
                            elif (activity in self.COASTAL_ACTIVITIES
                                    and loc.lower() in self.COASTAL_CITIES
                                    and weather in ("raining", "snowing")):
                                coastal_bad_template = [
                                    f"No, I wouldn't recommend you to go {activity} in {loc} "
                                    f"since it's {weather} {time}.",
                                    f"How unlucky, it's {weather} {time}. Maybe next time!"
                                ]
                                print(random.choice(coastal_bad_template))
                                return
                            elif activity in self.COASTAL_ACTIVITIES:
                                suggestions = self.citySuggestions(self.COASTAL_CITIES)

                                loc_prog_template = [
                                    f"{suggestions} are nice cities for {activity}--you should check them out.",
                                    f"I think {suggestions} are great places for {activity} instead.",
                                    f"{suggestions} are some good cities for that."
                                ]
                                loc_template = [
                                    f"{suggestions} are nice cities to {activity}--you should check them out.",
                                    f"I think {suggestions} are great places to {activity} instead.",
                                    f"If you want to {activity}, {suggestions} are some good cities for that."
                                ]
                                print(f"No, because {loc} is not a coastal city. "
                                      f"{self.recommendStr(activity, loc_prog_template, loc_template)}")
                                return

                            if activity in self.CLEAR_ACTIVITIES and weather not in ("raining", "snowing"):
                                print(random.choice(good_template))
                                return
                            elif weather in ("raining", "snowing"):
                                bad_weather_template = [
                                    f"The weather {time} is {weather}, which may ruin your experience, "
                                    f"so I suggest you go {activity} another time.",
                                    f"Not only do certain activities become potentially dangerous, "
                                    f"the weather {time} is {weather}, which makes "
                                    f" it a bad time to go {activity} {time}."
                                ]
                                print(random.choice(bad_weather_template))
                                return

                            if (activity in self.SNOW_ACTIVITIES and weather == "snowing"):
                                print(f"It's snowing in {loc} {time}? You better take advantage of this opportunity!")
                            elif (activity in self.SNOW_ACTIVITIES and weather != "snowing"):
                                print(f"How are you going to go {activity} in {loc} {time} when it's not even snowing?")
                            elif activity not in self.SNOW_ACTIVITIES and weather == "snowing":
                                print(f"It's snowing in {loc}, CA! But that means you can't go {activity} here!")
                            else:
                                # We should not be here
                                print(f"Something went wrong... your sentence may have been worded funny.")
                            return

                        else:
                            bad_wind_template = [
                                f"The wind speed in {loc} is {wind} mph {time}, which may ruin your experience. "
                                f"I suggest you go {activity} another time.",
                                f"Not only do certain activities become potentially dangerous, a {wind} mph wind speed "
                                f"also makes it a bad time to go {activity} {time}."
                            ]
                            print(random.choice(bad_wind_template))

            elif not self.needsRec:
                if not self.hasActivity and not self.hasLocation and not self.hasTime:
                    suggestions = self.citySuggestions(self.HOTSPOTS)
                    loc_rec_template = [
                        f"{suggestions} are all great cities to visit!",
                        f"There are some great things to do in {suggestions}!",
                        f"{suggestions} are some of the most popular locations in California. "
                        f"You should check them out!"
                    ]
                    print(random.choice(loc_rec_template))

                elif self.hasActivity and not self.hasLocation and self.hasTime:
                    activity = self.requestInfo["activity"]
                    print(f"Sounds fun! Where will you go {activity}?")

                elif self.hasActivity and not self.hasLocation and not self.hasTime:
                    activity = self.requestInfo["activity"]
                    print(f"When do you plan to go {activity} in?")

                elif self.hasActivity and self.hasLocation and not self.hasTime:
                    activity = self.requestInfo["activity"]
                    loc = self.formatCityName(
                        self.getLocation()
                    )
                    print(f"When do you plan to go {activity} in {loc}?")

                elif self.hasActivity and self.hasLocation and self.hasTime:
                    activity = self.requestInfo["activity"]
                    loc = self.formatCityName(
                        self.getLocation()
                    )
                    time = self.requestInfo["time"]

                    temp, weather, wind = self.getCityInfo(loc, time)
                    good_template = [
                        f"{loc} is a great place to go {activity} {time}.",
                        f"You should definitely go {activity} there. Great choice!",
                        f"I see nothing wrong with that. Enjoy your trip!"
                    ]

                    if temp != "unknown" and float(temp) < 50:
                        print(f"The temperature is {temp}F, which is too cold for "
                              f"most activities (except snowy ones).")
                    else:
                        if wind != "unknown" and float(wind) < 20:
                            weather = self.weatherAdj(self.getWeather(loc, time))

                            if (activity in self.COASTAL_ACTIVITIES
                                    and loc.lower() in self.COASTAL_CITIES
                                    and weather not in ("raining", "snowing")):
                                print(random.choice(good_template))
                                return
                            elif (activity in self.COASTAL_ACTIVITIES
                                  and loc.lower() in self.COASTAL_CITIES
                                  and weather in ("raining", "snowing")):
                                coastal_bad_template = [
                                    f"No, I wouldn't recommend you to go {activity} in {loc} "
                                    f"since it's {weather} {time}.",
                                    f"How unlucky, it's {weather} {time}. Maybe next time!"
                                ]
                                print(random.choice(coastal_bad_template))
                                return
                            elif activity in self.COASTAL_ACTIVITIES:
                                suggestions = self.citySuggestions(self.COASTAL_CITIES)

                                loc_prog_template = [
                                    f"{suggestions} are nice cities for {activity}--you should check them out.",
                                    f"I think {suggestions} are great places for {activity} instead.",
                                    f"{suggestions} are some good cities for that."
                                ]
                                loc_template = [
                                    f"{suggestions} are nice cities to {activity}--you should check them out.",
                                    f"I think {suggestions} are great places to {activity} instead.",
                                    f"If you want to {activity}, {suggestions} are some good cities for that."
                                ]
                                print(f"{loc} is not a coastal city. "
                                      f"{self.recommendStr(activity, loc_prog_template, loc_template)}")
                                return

                            if (activity in self.CLEAR_ACTIVITIES and weather not in ("raining", "snowing")):
                                print(random.choice(good_template))
                                return
                            elif weather in ("raining", "snowing"):
                                bad_weather_template = [
                                    f"The weather {time} is {weather}, which may ruin your experience, "
                                    f"so I suggest you go {activity} another time.",
                                    f"Not only do certain activities become potentially dangerous, "
                                    f"the weather {time} is {weather}, which makes it a bad time to go {activity} {time}."
                                ]
                                print(random.choice(bad_weather_template))
                                return

                            if (activity in self.SNOW_ACTIVITIES and weather == "snowing"):
                                print(f"It's snowing in {loc} {time}? You better take advantage of this opportunity!")
                            elif (activity in self.SNOW_ACTIVITIES and weather != "snowing"):
                                print(f"How are you going to go {activity} in {loc} {time} when it's not even snowing?")
                            elif activity not in self.SNOW_ACTIVITIES and weather == "snowing":
                                print(f"It's snowing in {loc}, CA! But that means you can't go {activity} here!")
                            else:
                                # We should not be here
                                print(f"Something went wrong... your sentence may have been worded funny.")
                            return

                        else:
                            bad_wind_template = [
                                f"The wind speed in {loc} is {wind} mph {time}, which may ruin your experience. "
                                f"I suggest you go {activity} another time.",
                                f"Not only do certain activities become potentially dangerous, a {wind} mph wind speed "
                                f"also makes it a bad time to go {activity} {time}."
                            ]
                            print(random.choice(bad_wind_template))

                    if activity in self.COASTAL_ACTIVITIES and loc.lower() not in self.COASTAL_CITIES:
                        print(f"{loc} isn't a coastal city, so you can't go {activity} there!")
                    else:
                        print(f"That's good for you. When will you go {activity}?")

                else:
                    print("Something went wrong... your sentence may have been worded funny.")

            elif self.comparing:
                loc = self.formatCityName(
                    self.getLocation()
                )

                time = self.requestInfo["time"]
                time0 = self.requestInfo["time0"]
                temp = self.getTemperature(loc, time)
                temp0 = self.getTemperature(loc, time0)
                comp = self.requestInfo["compareWord"]

                if comp in ("hotter", "warmer"):
                    if temp > temp0:
                        print(f"Yes, {time} is {comp} than {time0} in {loc}. "
                              f"It is {temp}F {time} and {temp0}F {time0}.")
                    else:
                        print(f"No, {time} is not {comp} than {time0} in {loc}. "
                              f"It is {temp}F {time} and {temp0}F {time0}.")
                else:
                    if temp < temp0:
                        print(f"Yes, {time} is {comp} than {time0} in {loc}. "
                              f"It is {temp}F {time} and {temp0}F {time0}.")
                    else:
                        print(f"No, {time} is not {comp} than {time0} in {loc}. "
                              f"It is {temp}F {time} and {temp0}F {time0}.")

        else:
            invalid_templates = [
                "Sorry, I didn't understand what you said. Can you rephrase that again?",
                "Can you rephrase that again? I didn't understand that sentence."
            ]
            print(random.choice(invalid_templates))

    ############### UTILITY FUNCTIONS #########################################
    def getTemperature(self, location: str, time: str):
        """
        Returns the temperature float value in location as a string,
        and returns 'unknown' if it could not be fetched.
        """
        return self.getCityInfo(location, time)[0]

    def getWeather(self, location: str, time: str):
        """Returns the weather in location, and returns 'unknown' if it could not be fetched."""
        return self.getCityInfo(location, time)[1]

    def getWind(self, location: str, time: str):
        """
        Returns the wind speed float value in location as a string,
        and returns 'unknown' if it could not be fetched.
        """
        return self.getCityInfo(location, time)[2]

    def getLocation(self):
        """Returns the location in lowercase, and empty string if location doesn't exist."""
        if self.requestInfo["location"]:
            return self.requestInfo["location"]
        elif self.requestInfo["locPrefix"] and self.requestInfo["locSuffix"]:
            return f"{self.requestInfo['locPrefix']} {self.requestInfo['locSuffix']}"
        else:
            return ""

    def getCityInfo(self, location: str, time: str):
        """
        Uses the OWMWrapper object to get weather if it doesn't exist in local DB already.
        Returns "unknown" if location/temp doesn't exist.
        We can't handle "week" here since this function only returns one value.
        """
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
            wind = self.Wrapper.getCityWind(location, t)
            if self.DEBUG:
                print(f"getTemperature {temp}F {weather} {wind}mph")

            # getCityTemp returns NaN if couldn't get temperature
            if temp == temp and weather != "unknown" and wind != "unknown":
                return temp, weather, wind

        return "unknown", "unknown", "unknown"

    def formatCityName(self, city: str):
        """Capitalizes first letter in city names. Ex: san jose -> San Jose, irvine -> Irvine"""
        return " ".join([s.capitalize() for s in city.split()])

    def weatherAdj(self, weather: str):
        """Gets the adjective word of weather. Ex: clouds -> cloudy, clear -> sunny (both are the same)"""
        if weather in self.WEATHER_ADJS:
            return self.WEATHER_ADJS[weather]
        else:
            return weather

    def citySuggestions(self, locs: str, a=True):
        """
        Gets list of locations, randomly chooses a few, and returns as a string.
        For formatting purposes, the 'a' parameter defines whether the joining word is "and" or "or".
        """
        locs = tuple(locs)
        join = "and" if a else "or"
        cities = set((self.formatCityName(c) for c in random.sample(locs, random.randint(1, 3))))
        city = self.formatCityName(random.choice(locs))
        while city in cities:
            city = self.formatCityName(random.choice(locs))
        return f"{', '.join(cities)} {join} {city}"

    def recommendStr(self, activity: str, ing_template: List[str], template: List[str]):
        """Returns the correct template based on whether 'activity' is the progressive tense of the verb."""
        if activity[-3:] == "ing":
            return random.choice(ing_template)
        else:
            return random.choice(template)

    def resetStatus(self):
        """Resets the chatbot state after every user query."""
        self.comparing = False
        self.hasLocation = False
        self.hasActivity = False
        self.hasTime = False
        self.needsRec = False
        self.question = False
        self.weatherQuery = False
        self.hasWeatherWord = False
        self.isGreeting = False
        self.invalidLocation = False
        self.requestInfo["compare"] = None
        self.requestInfo["time0"] = ""


if __name__ == "__main__":
    user_in = ""
    c = VacationBot(VacationParser(), OWMWrapper(), True)   # remove third param to disable debugging
    while user_in not in ("goodbye", "bye", "bye-bye"):
        user_in = input("User>")
        c.say(user_in)
        c.reply()

