from pypdf import PdfReader
import urllib.request
import re
import pprint
from re import sub
from os import system, name ,path
import math
import csv

class app():
    def __init__(self):
    # list of airports in South Africa
        self.AIRPORTS = {}
        self.index , self.notams, self.date = self.loadinPdf("notam.pdf")
        self.main()

    def csv_to_dict(self,file_path):
        """
        Reads a CSV file and returns a dictionary with the first column as keys
        and the second column as values.

        Args:
            file_path (str): The path to the CSV file.

        Returns:
            dict: A dictionary with the CSV data.
        """
        result_dict = {}
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    if len(row) == 2:  # Ensure each row has exactly two columns
                        key, value = row
                        result_dict[key.strip()] = value.strip()
                    else:
                        print(f"Skipping invalid row: {row}")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return result_dict

    def updatenotams(self):
        urllib.request.urlretrieve("https://caasanwebsitestorage.blob.core.windows.net/notam-summaries-and-pib/SUMMARY.pdf", "notam.pdf")

    def split_with_multiple_delimiters(self,string, delimiters):
        # Join delimiters into a regex pattern
        regex_pattern = '|'.join(map(re.escape, delimiters))
        # Use re.split to split the string by the regex pattern
        return re.split(regex_pattern, string)

    def loadinPdf(self,filename):
        # creating a pdf reader object
        reader = PdfReader(filename)
        PDF_LENGTH = len(reader.pages)
        notams = []
        index = {}
        text= ""

        page = reader.pages[0]
        firsttext = page.extract_text()
        num =firsttext.find("Date/Time")
        date = firsttext[num+10:num+22]
        num =firsttext.find("Briefing Id")
        id = firsttext[num+11:num+23]

        for a in range(1,PDF_LENGTH):
            # getting a specific page from the pdf file
            page = reader.pages[a]

            # extracting text from page
            text += page.extract_text()

        text = re.sub(id[1:9]+" - "+date+" ATNS .*/"+str(PDF_LENGTH), '',text)

        temp = text.split('NOTAMN')
        
        for i in range(0,len(temp)-1):
            temp[i+1] = temp[i][-9:] + 'NOTAMN'+temp[i+1]
        temp = temp[1:]


        for i in range(0,len(temp)):
            temp[i] = self.split_with_multiple_delimiters(temp[i], ["Q) ","A) ","B) ","C) ","D) ","E) ","F) ","G) "])
            temp[i][-1] = temp[i][-1][:-10]
        notams += temp
        
        for i, notam in enumerate(notams):
            codes = notam[2].split(' ')
            
            for _, code in enumerate(codes):
                if code not in index.keys() and code != "":
                    index[code] = [i] #list(i)
                elif code != "":
                    temp = index[code]
                    index[code]= temp + [i]
        return index , notams, date

    def display_menu(self,date):
        self.clear()
        """
        Display the main menu.
        """
        print("\n" + "=" * 60)
        print("\tNOTAM Finder\t\tUpdated Date : " + date)
        print("=" * 60)
        print("1. Search for NOTAMs")
        print("2. Search for NOTAMs with buffer area")
        print("3. Update NOTAMs")
        print("4. Exit")
        print("=" * 60)

    def fetch_notams(self,icao_code):
        output = []
        if icao_code.upper() not in self.index.keys():
            return ["No NOTAMS found for "+icao_code+"."]
        fetch = self.index[icao_code]
        for _ ,a in enumerate(fetch):
            output.append( self.notams[a])
        return output

    def parse_coordinate(self,coord):
        """
        Parse a coordinate in the format ddmmSdddmmE and return decimal degrees.
        """

        lat_deg = int(coord[:2])
        lat_min = int(coord[2:4])
        lat_sign = -1 if coord[4] == 'S' else 1

        lon_deg = int(coord[5:8])
        lon_min = int(coord[8:10])
        lon_sign = -1 if coord[10] == 'W' else 1

        lat = lat_sign * (lat_deg + lat_min / 60.0)
        lon = lon_sign * (lon_deg + lon_min / 60.0)
        radius = int(coord[11:])
        return lat, lon, radius

    def haversine_distance(self,lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on Earth using the Haversine formula.
        """
        R = 6371.0  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # Distance in kilometers

    def circles_intersect(self,coord1, coord2, buffer):
        """
        Determine if two circles intersect based on their coordinates and radii.

        Args:
            coord1 (str): Latitude/longitude of the first circle in ddmmSdddmmE format.
            radius1 (float): Radius of the first circle in kilometers.
            coord2 (str): Latitude/longitude of the second circle in ddmmSdddmmE format.
            radius2 (float): Radius of the second circle in kilometers.

        Returns:
            bool: True if the circles intersect, False otherwise.
        """
        # Parse the coordinates
        lat1, lon1, radius1 = self.parse_coordinate(coord1)
        lat2, lon2, radius2 = self.parse_coordinate(coord2)

        # Calculate the distance between the two points
        distance = self.haversine_distance(lat1, lon1, lat2, lon2)

        # Check if the distance is less than or equal to the sum of the radii
        return distance <= (radius1 + radius2 + buffer)

    def fetch_notams_with_buffer(self,icao_code,buffer):
        #circles_intersect("3259S01810E001", "3257S01803E001", 5)
        if icao_code.upper() not in self.AIRPORTS.keys():
            return ["No NOTAMS found for "+icao_code+"."]
        coordport = self.AIRPORTS[icao_code.upper()]
        output= []
        outnums=[]
        outnums = self.index[icao_code]
        for i , a in enumerate(self.notams):
            notamcoord = a[1].split("/")[-1]
            if self.circles_intersect(coordport, notamcoord, buffer):
                if i not in outnums:
                    outnums.append(i)
        for _,a in enumerate(outnums):
            output.append( self.notams[a])
        return output

    def clear(self):

        # for windows
        if name == 'nt':
            _ = system('cls')

        # for mac and linux(here, os.name is 'posix')
        else:
            _ = system('clear')

    def printnotam(self,notam):
        if type(notam) is not list:
            return notam
        codes = ["Q)","A)","B)","C)","D)","E)","F)","G)"]
        output = ''
        for i , a in enumerate(notam):
            if i == 0:
                output = notam[0]+"\n"
            else:
                output += "\t"+codes[i-1]+" "+notam[i]
        return output

    def main(self):
        """
        Main function to run the NOTAM finder application.
        """
        if path.isfile('airports.csv'):
            self.AIRPORTS = self.csv_to_dict('airports.csv')
        else:
            print("\n" + "=" * 60)
            print("\tNOTAM Finder\t\t")
            print("=" * 60)
            print("An error occurred : No 'airports.csv' file found")
            print("Failed to load airport data, please copy file to folder root")
            return

        if not(path.isfile('notam.pdf')):
            self.updatenotams()
        self.display_menu(self.date)
        while True:

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                icao_code = input("\nEnter ICAO airport code (e.g., FALA): ").strip()
                if len(icao_code) != 4 or not icao_code.isalpha():
                    print("Invalid ICAO code. Please enter a 4-letter code.")
                    continue
                    

                print(f"\nFetching NOTAMs for {icao_code.upper()}...\n")
                notams = self.fetch_notams(icao_code.upper())
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.printnotam(notam)}\n")
                    continue

            if choice == "2":
                ans = input("\nEnter ICAO airport code and buffer(km)(e.g., FALA 5): ").strip().split()
                if len(ans) <2 :
                    print("Invalid format please Enter ICAO airport code and buffer(km)(e.g., FALA 5): ")
                    continue
                icao_code = ans[0]
                buffer = int(ans[1])
                if len(icao_code) != 4 or not icao_code.isalpha() or icao_code.upper() not in self.AIRPORTS.keys():
                    print("Invalid ICAO code. Please enter a 4-letter code.")
                    continue

                print(f"\nFetching NOTAMs for {icao_code.upper()}...\n")
                notams = self.fetch_notams_with_buffer(icao_code.upper(),buffer)
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.printnotam(notam)}\n")

            elif choice == "3":
                print("\nUpdating the notams to the latest version...")
                self.updatenotams()
                self.display_menu(self.Date)
            elif choice == "4":
                print("\nExiting the application. Safe travels!")
                break

            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    app = app()
    app.__init__()