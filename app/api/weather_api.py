import requests

def getWeatherConditions(city):
	r = requests.get("http://api.wunderground.com/api/412316f799ba57c0/conditions/q/CA/" + city + ".json")
	
	weather = r.json()["current_observation"]

	weatherObj = {}
	weatherObj["city"] = weather["display_location"]["city"]
	weatherObj["weather"] = weather["weather"].lower()
	weatherObj["temperature"] = weather["temperature_string"]
	return weatherObj