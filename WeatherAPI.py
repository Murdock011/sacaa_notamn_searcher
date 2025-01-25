import gzip
import shutil
import urllib.request
from os import path
import pprint
import csv
import datetime


class weatherAPI():
	def __init__(self):
		if not path.isfile('metars.cache.csv') or not path.isfile('tafs.cache.csv'):
			self.update_weather()
		self.meatars, self.tafs = self.loadweather()

	def getTaf(self,icao):
		try:	
			return self.tafs[icao.upper()]
		except Exception as e:
			return False

	def getMetar(self,ico):
		try:
			return self.meatars[icao.upper()]
		except Exception as e:
			return False

	def getUpdatedDate(self):
		return self.meatars['DATE']

	def loadweather(self):
		types = ["metars","tafs"]
		result_list = []
		for t in types:
			result_dict = {}
			if not path.isfile(f'{t}.csv'):
				with open(f'{t}.cache.csv', mode='r', encoding='utf-8') as csv_file:
					reader = csv.reader(csv_file)
					for i , row in enumerate(reader):
						if i >5:
							value = row[0]
							key = value[:4]
							if key == "TAF ":
								key = value[4:8]
							if key == "AMD " or key == "COR":
								key = value[8:12]
							result_dict[key.strip()] = value.strip() 
							with open(f'{t}.csv', 'w') as csv_file:
								csv_file.write(f"DATE {datetime.datetime.now().strftime("%d%b%y %H%M %z")} \n")
								for a in list(result_dict.values() ):
									csv_file.write(a+"\n")

			else:
				with open(f'{t}.csv', mode='r', encoding='utf-8') as csv_file:
					reader = csv.reader(csv_file)
					for i , row in enumerate(reader):
						value = row[0]
						key = value[:4]
						if key == "TAF ":
							key = value[4:8]
						if key == "AMD " or key == "COR":
							key = value[8:12]
						result_dict[key] = value
			result_list.append(result_dict)	
		return result_list[0],result_list[1]

						

	def update_weather(self):
		urllib.request.urlretrieve(
				"https://aviationweather.gov/data/cache/metars.cache.csv.gz",
				"metars.cache.csv.gz",
			)
		with gzip.open('metars.cache.csv.gz', 'rb') as f_in:
			with open('metars.cache.csv', 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)

#https://aviationweather.gov/data/cache/tafs.cache.csv.gz
			urllib.request.urlretrieve(
				"https://aviationweather.gov/data/cache/tafs.cache.csv.gz",
				"tafs.cache.csv.gz",
			)
		with gzip.open('tafs.cache.csv.gz', 'rb') as f_in:
			with open('tafs.cache.csv', 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)

if __name__ == "__main__":
	weather = weatherAPI()
	print(weather.getTaf('faor'))