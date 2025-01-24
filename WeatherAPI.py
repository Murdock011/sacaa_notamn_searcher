import gzip
import shutil
import urllib.request
from os import path
import pprint
import csv


class weatherAPI():
	def __init__(self):
		if not path.isfile('metars.cache.csv.gz'):
			self.update_weather()

	def loadweather(self):
			


		result_dict = {}
		with open('metars.cache.csv', mode='r', newline='', encoding='utf-8') as csv_file:
			reader = csv.reader(csv_file)
			for i , row in enumerate(reader):
				if i >5:
					value = row[0]
					key = value[:4]
					result_dict[key.strip()] = value.strip() 
		pprint.pp(result_dict["FALW"])

						

	def update_weather(self):
		urllib.request.urlretrieve(
				"https://aviationweather.gov/data/cache/metars.cache.csv.gz",
				"metars.cache.csv.gz",
			)
		with gzip.open('metars.cache.csv.gz', 'rb') as f_in:
			with open('metars.cache.csv', 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)




if __name__ == "__main__":
	weather = weatherAPI()
	weather.loadweather()