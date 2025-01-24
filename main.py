from os import system, name
import logging
from NotamAPI import notamAPI


class App:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            filename="notam_finder_App.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.info("Application started.")

        self.NotamsAPI = notamAPI()

        self.main()


    def display_menu(self):
        """Display the main menu."""
        self.clear()
        print("\n" + "=" * 60)
        print(f"\tNOTAM Finder\t\tUpdated Date: {self.NotamsAPI.getUpdatedDate()}")
        print("=" * 60)
        print("1. Search for NOTAMs")
        print("2. Search for NOTAMs with buffer area")
        print("3. Update NOTAMs")
        print("4. Exit")
        print("=" * 60)


    def clear(self):
        """Clear the terminal screen."""
        try:
            if name == 'nt':
                _ = system('cls')  # Windows
            else:
                _ = system('clear')  # Mac and Linux
        except Exception as e:
            logging.error(f"Failed to clear the screen: {e}")


    def main(self):
        """Main function to run the NOTAM finder application."""
        self.display_menu()

        while True:
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.display_menu()
                icao_code = input("\nEnter ICAO airport code (e.g., FALA): ").strip()
                if len(icao_code) != 4 or not icao_code.isalpha():
                    print("Invalid ICAO code. Please enter a 4-letter code.")
                    logging.warning(f"Invalid ICAO code entered: {icao_code}")
                    continue

                print(f"\nFetching NOTAMs for {icao_code.upper()}...\n")
                notams = self.NotamsAPI.fetch_notams(icao_code.upper())
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.NotamsAPI.printnotam(notam)}\n")

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
                notams = self.NotamsAPI.fetch_notams_with_buffer(icao_code.upper(), buffer)
                for idx, notam in enumerate(notams, start=1):
                    print(f"{idx}. {self.NotamsAPI.printnotam(notam)}\n")

            elif choice == "3":
                print("\nUpdating NOTAMs to the latest version...")
                self.NotamsAPI.update_notams()
                self.display_menu()

            elif choice == "4":
                print("\nExiting the application. Safe travels!")
                logging.info("Application exited.")
                break

            else:
                self.display_menu()
                print("Invalid choice. Please try again.")
                logging.warning(f"Invalid menu choice entered: {choice}")

if __name__ == "__main__":
    app = App()
