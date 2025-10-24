"""
Main script to scrape Markov inventory and upload to PostgreSQL
"""
import os
import sys
from datetime import datetime
from scrape_markov_inventory import scrape_markov_inventory
from upload_to_postgres import upload_inventory_to_postgres, test_connection


def main():
    """
    Main function to orchestrate scraping and uploading inventory data.
    """
    print("=" * 60)
    print("Markov Inventory Scraper & PostgreSQL Uploader")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Step 1: Test database connection
        print("Step 1: Testing database connection...")
        if not test_connection():
            print("ERROR: Database connection failed. Please check DATABASE_URL.")
            return 1
        print()

        # Step 2: Scrape inventory data
        print("Step 2: Scraping inventory data from Markov...")
        inventory_data = scrape_markov_inventory(company=os.getenv('MARKOV_COMPANY', ''), email=os.getenv('MARKOV_EMAIL', ''), password=os.getenv('MARKOV_PASSWORD'))

        if not inventory_data:
            print("WARNING: No inventory data scraped. Exiting.")
            return 0

        print(f"Successfully scraped {len(inventory_data)} inventory items\n")

        # Step 3: Upload to PostgreSQL
        print("Step 3: Uploading data to PostgreSQL...")
        records_uploaded = upload_inventory_to_postgres(inventory_data)

        print("\n" + "=" * 60)
        print(f"✓ SUCCESS: {records_uploaded} records uploaded to database")
        print("=" * 60)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        return 130

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ ERROR: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
