from pypdf import PdfReader
import urllib.request
import re
import pprint
from re import sub
from os import system, name, path
import math
import csv
import logging

class App:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            filename="notam_finder.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.info("Application started.")

        # Ensure the NOTAM file is available
        if not path.isfile('notam.pdf'):
            self.update_notams()

        # Load airports data and NOTAM information
        self.AIRPORTS = {}
        self.index, self.notams, self.date = self.load_pdf("notam.pdf")
        self.main()

    def csv_to_dict(self, file_path):
        """
        Reads a CSV file and returns a dictionary with the first column as keys
        and the second column as values.
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
                        logging.warning(f"Skipping invalid row: {row}")
        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        return result_dict

    def update_notams(self):
        """Download the latest NOTAM PDF and reload the data."""
        try:
            logging.info("Downloading the latest NOTAM PDF.")
            urllib.request.urlretrieve(
                "https://caasanwebsitestorage.blob.core.windows.net/notam-summaries-and-pib/SUMMARY.pdf",
                "notam.pdf",
            )
            self.index, self.notams, self.date = self.load_pdf("notam.pdf")
        except Exception as e:
            logging.error(f"Failed to update NOTAMs: {e}")

    def split_with_multiple_delimiters(self, string, delimiters):
        """Split a string using multiple delimiters."""
        regex_pattern = '|'.join(map(re.escape, delimiters))
        return re.split(regex_pattern, string)

    def load_pdf(self, filename):
        """Load and parse NOTAM data from the PDF file."""
        try:
            reader = PdfReader(filename)
            PDF_LENGTH = len(reader.pages)
            notams = []
            index = {}
            text = ""

            # Extract date and briefing ID from the first page
            page = reader.pages[0]
            first_text = page.extract_text()
            num = first_text.find("Date/Time")
            date = first_text[num + 10:num + 22]
            num = first_text.find("Briefing Id")
            briefing_id = first_text[num + 11:num + 23]

            # Extract NOTAM content from subsequent pages
            for a in range(1, PDF_LENGTH):
                page = reader.pages[a]
                text += page.extract_text()

            text = re.sub(briefing_id[1:9] + " - " + date + " ATNS .*/" + str(PDF_LENGTH), '', text)
            temp = text.split('NOTAMN')

            for i in range(0, len(temp) - 1):
                temp[i + 1] = temp[i][-9:] + 'NOTAMN' + temp[i + 1]
            temp = temp[1:]

            for i in range(0, len(temp)):
                temp[i] = self.split_with_multiple_delimiters(temp[i], ["Q) ", "A) ", "B) ", "C) ", "D) ", "E) ", "F) ", "G) "])
                temp[i][-1] = temp[i][-1][:-10]
            notams += temp

            for i, notam in enumerate(notams):
                codes = notam[2].split(' ')
                for _, code in enumerate(codes):
                    if code not in index.keys() and code != "":
                        index[code] = [i]
                    elif code != "":
                        temp = index[code]
                        index[code] = temp + [i]
            return index, notams, date

        except Exception as e:
            logging.error(f"Failed to load PDF: {e}")
            return {}, [], "Unknown"

    def display_menu(self):
        """Display the main menu."""
        self.clear()
        print("\n" + "=" * 60)
        print(f"\tNOTAM Finder\t\tUpdated Date: {self.date}")
        print("=" * 60)
        print("1. Search for NOTAMs")
        print("2. Search for NOTAMs with buffer area")
        print("3. Update NOTAMs")
        print("4. Exit")
        print("=" * 60)

    def fetch_notams(self, icao_code):
        """Fetch NOTAMs for a specific ICAO code."""
        output = []
        if icao_code.upper() not in self.index.keys():
            return [f"No NOTAMS found for {icao_code}."]
        fetch = self.index[icao_code]
        for _, a in enumerate(fetch):
            output.append(self.notams[a])
        return output

    def parse_coordinate(self, coord):
        """Parse a coordinate string in ddmmSdddmmE format."""
        try:
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
        except Exception as e:
            logging.error(f"Failed to parse coordinate: {coord}. Error: {e}")
            return None, None, 0

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate the great-circle distance using the Haversine formula."""
        R = 6371.0  # Earth's radius in kilometers
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def circles_intersect(self, coord1, coord2, buffer):
        """Check if two NOTAM circles intersect."""
        lat1, lon1, radius1 = self.parse_coordinate(coord1)
        lat2, lon2, radius2 = self.parse_coordinate(coord2)
        if lat1 is None or lat2 is None:
            return False
        distance = self.haversine_distance(lat1, lon1, lat2, lon2)
        return distance <= (radius1 + radius2 + buffer)

    def fetch_notams_with_buffer(self, icao_code, buffer):
        """Fetch NOTAMs within a buffer area for a specific ICAO code."""
        if icao_code.upper() not in self.AIRPORTS:
            logging.warning(f"No airport data found for ICAO code: {icao_code}.")
            return [f"No NOTAMs found for {icao_code}."]

        coordport = self.AIRPORTS[icao_code.upper()]
        output = []
        outnums = set(self.index.get(icao_code.upper(), []))  # Use a set to avoid duplicates

        for i, notam in enumerate(self.notams):
            try:
                notamcoord = notam[1].split("/")[-1]
                if self.circles_intersect(coordport, notamcoord, buffer):
                    outnums.add(i)
            except Exception as e:
                logging.error(f"Error processing NOTAM {i}: {e}")

        for idx in sorted(outnums):  # Ensure consistent ordering
            output.append(self.notams[idx])

        logging.info(f"Fetched {len(output)} NOTAMs for {icao_code.upper()} with buffer {buffer} km.")
        return output

    def clear(self):
        """Clear the terminal screen."""
        try:
            if name == 'nt':
                _ = system('cls')  # Windows
            else:
                _ = system('clear')  # Mac and Linux
        except Exception as e:
            logging.error(f"Failed to clear the screen: {e}")

    def printnotam(self, notam):
        """Format a NOTAM for display."""
        if not isinstance(notam, list):
            return notam

        codes = ["Q)", "A)", "B)", "C)", "D)", "E)", "F)", "G)"]
        output = ""

        for i, content in enumerate(notam):
            if i == 0:
                output = f"{content}\n"
            else:
                output += f"\t{codes[i - 1]} {content.strip()}\n"

        return output.strip()

    def main(self):
        """Main function to run the NOTAM finder application."""
        if not path.isfile('airports.csv'):
            print("\n" + "=" * 60)
            print("\tNOTAM Finder\t\t")
            print("=" * 60)
            print("Error: 'airports.csv' file not found.")
            print("Please copy the file to the application's root folder.")
            logging.error("Airports CSV file missing. Application terminated.")
            return

        self.AIRPORTS = self.csv_to_dict('airports.csv')
        self.display_menu()

        while True:
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                icao_code = input("\nEnter ICAO airport code (e.g., FALA): ").strip()
                if len(icao_code) != 4 or not icao_code.isalpha():
                    print("Invalid ICAO code. Please enter a 4-letter code.")
                    logging.warning(f"Invalid ICAO code entered: {icao_code}")
                    continue

                print(f"\nFetching NOTAMs for {icao_code.upper()}...\n")
                notams = self.fetch_notams(icao_code.upper())
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.printnotam(notam)}\n")

            elif choice == "2":
                ans = input("\nEnter ICAO airport code and buffer (e.g., FALA 5): ").strip().split()
                if len(ans) < 2:
                    print("Invalid format. Please enter ICAO airport code and buffer (e.g., FALA 5).")
                    logging.warning("Invalid input format for buffer search.")
                    continue

                icao_code, buffer = ans[0], ans[1]
                if not buffer.isdigit():
                    print("Buffer must be an integer (e.g., FALA 5).")
                    logging.warning(f"Invalid buffer value: {buffer}")
                    continue

                buffer = int(buffer)
                if len(icao_code) != 4 or not icao_code.isalpha():
                    print("Invalid ICAO code. Please enter a 4-letter code.")
                    logging.warning(f"Invalid ICAO code entered: {icao_code}")
                    continue

                print(f"\nFetching NOTAMs for {icao_code.upper()} with buffer {buffer} km...\n")
                notams = self.fetch_notams_with_buffer(icao_code.upper(), buffer)
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.printnotam(notam)}\n")

            elif choice == "3":
                print("\nUpdating NOTAMs to the latest version...")
                self.update_notams()
                self.display_menu()

            elif choice == "4":
                print("\nExiting the application. Safe travels!")
                logging.info("Application exited.")
                break

            else:
                print("Invalid choice. Please try again.")
                logging.warning(f"Invalid menu choice entered: {choice}")

if __name__ == "__main__":
    app = App()
    app.__init__()
