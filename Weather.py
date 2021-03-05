import requests


class OWMWrapper:
    # I won't bother hiding an API key for a free service
    API_KEY = "30f3e68d6b3d946845b35b392fc8b8f9"
    LINK = f"http://api.openweathermap.org/data/2.5/"
    CUR_REQ = "weather?"
    WEEK_REQ = "onecall?"
    PARAMS = {
        "q": "",
        "units": "imperial",
        "APPID": API_KEY
    }

    def __init__(self):
        # 0-7 in the value dict indicates which day since today. 0 is today, 1 is tomorrow, 7 is next week
        self.DB = {}

    # Sends a request for temperature and weather of city.
    # Returns status code
    def get(self, city: str):
        if city not in self.DB:
            city = city.lower()
            link = self.LINK + self.CUR_REQ

            self.PARAMS["q"] = f"{city},ca,us"
            for p in self.PARAMS:
                link += f"{p}={self.PARAMS[p]}&"
            r = requests.get(link)
            status_code = r.status_code
            if status_code == 200:
                r = r.json()
                d = {0: {"temp": r["main"]["temp"],
                         "weather": r["weather"][0]["main"].lower(),
                         "wind": r["wind"]["speed"]
                         }
                     }
                self.DB[city] = d
            return status_code

    # gets the weekly forecast for a city
    def getWeekly(self, city: str):
        city = city.lower()

        link = self.LINK + self.CUR_REQ
        self.PARAMS["q"] = f"{city},ca,us"
        for p in self.PARAMS:
            link += f"{p}={self.PARAMS[p]}&"
        r = requests.get(link)
        status_code = r.status_code
        if status_code == 200:
            r = r.json()

            # build weekly request link
            week_params = dict(self.PARAMS)
            del week_params["q"]
            week_params["exclude"] = "current,minutely,hourly,alerts"
            week_params["lat"] = r["coord"]["lat"]
            week_params["lon"] = r["coord"]["lon"]

            week_link = self.LINK + self.WEEK_REQ
            for p in week_params:
                week_link += f"{p}={week_params[p]}&"

            rq = requests.get(week_link)
            status_code = rq.status_code
            if status_code == 200:
                self.DB[city] = {}
                rq = rq.json()
                for day in range(len(rq["daily"])):
                    if day not in self.DB[city]:
                        self.DB[city][day] = {}
                    self.DB[city][day]["temp"] = rq["daily"][day]["temp"]["day"]
                    self.DB[city][day]["weather"] = rq["daily"][day]["weather"][0]["main"].lower()
                    self.DB[city][day]["wind"] = rq["daily"][day]["wind_speed"]

        return status_code

    def getCityTemp(self, city: str, t=0):
        """Gets city temperature for time t, where today = t = 0"""
        assert 0 <= t < 8, f"t was {t}"
        if city.lower() in self.DB:
            if t in self.DB[city]:
                return self.DB[city][t]["temp"]
        return float("NaN")

    def getCityWeather(self, city: str, t=0):
        """Gets city weather for time t, where today = t = 0"""
        assert 0 <= t < 8, f"t was {t}"
        if city.lower() in self.DB:
            if t in self.DB[city]:
                return self.DB[city][t]["weather"]
        return "unknown"

    """Gets city wind speed (in mph) for time t, where today = t = 0"""
    def getCityWind(self, city: str, t=0):
        assert 0 <= t < 8, f"t was {t}"
        if city.lower() in self.DB:
            if t in self.DB[city]:
                return self.DB[city][t]["wind"]
        return "unknown"

    def __str__(self):
        s = "OWMWrapper.DB(\n"
        for key, val in self.DB.items():
            s += f"\t{key}:\n"
            for k,v in val.items():
                s += f"\t\t{k}: {v}\n"
        s += ")"
        return s

if __name__ == "__main__":
    w = OWMWrapper()
    # get() or getWeekly() cities here
    w.get("irvine")


    # end
    print(w)







