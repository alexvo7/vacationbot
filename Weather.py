import requests


# I won't bother hiding an API key for a free service
class OWMWrapper:
    API_KEY = "30f3e68d6b3d946845b35b392fc8b8f9"
    "http://api.openweathermap.org/data/2.5/weather?q=London&units=imperial&APPID={APIKEY}"
    LINK = f"http://api.openweathermap.org/data/2.5/weather?"
    PARAMS = {
        "q": "",
        "units": "imperial",
        "APPID": API_KEY
    }

    MAJOR_CITIES = {
        "los angeles",
        "san francisco",
        "san jose",
        "san diego",
        "sacramento"
    }

    def __init__(self):
        self.DB = {d: {"temp": 0, "weather": ""} for d in self.MAJOR_CITIES}
        # for c in self.MAJOR_CITIES:
        #     self.get(c)

    # Sends a request for temperature and weather of city.
    # Returns status code
    def get(self, city):
        link = self.LINK
        city = city.lower()
        self.PARAMS["q"] = f"{city},ca,us"
        for p in self.PARAMS:
            link += f"{p}={self.PARAMS[p]}&"
        # print(link)
        r = requests.get(link)
        status_code = r.status_code
        r = r.json()
        if status_code == 200:
            d = {
                "temp": r["main"]["temp"],
                "weather": r["weather"][0]["main"]
            }
            self.DB[city] = d
        return status_code

    def __str__(self):
        s = "OWMWrapper.DB(\n"
        for k in w.DB:
            s += f"\t{k}: {w.DB[k]}\n"
        s += ")"
        return s

if __name__ == "__main__":
    w = OWMWrapper()
    w.get("")
    print(w)







