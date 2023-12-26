import csv
import yaml
import logging
import pandas as pd
from tqdm import tqdm
from sell_contract import WheelSell

logging.basicConfig(level="ERROR")

with open("config/config.yaml", "r") as stream:
    try:
        parser = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        logging.error(e)

class Wheeler:
    def __init__(self, option_data):
        self.symbol = option_data["symbol"]
        self.mktPrice = option_data["mktPrice"]
        self.strikeprice = option_data["strikeprice"]
        self.actualDelta = option_data["actualDelta"]
        self.premium = option_data["premium"]
        self.num_shares = option_data["numshares"]
        self.totpremium = self.num_shares * self.premium
        self.ror = option_data["ror"]
        self.expirydate = option_data["expirydate"]
        self.dte = option_data["dte"]
        self.annual_ror = option_data["annual_ror"]
        self.capital = self.strikeprice * self.num_shares
        self.open_int = option_data["open_int"]

        self.output_string = (
            "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
                self.symbol,
                self.mktPrice,
                self.strikeprice,
                self.actualDelta,
                self.premium,
                self.num_shares,
                self.totpremium,
                self.ror,
                self.expirydate,
                self.dte,
                self.annual_ror,
                self.capital,
                self.open_int
            )
        )
    
    def writeRowToCSV(self):
        output_list = self.output_string.split(",")
        try:
            with open(parser['OUTPUT_FILE'], "a", newline="", encoding="utf-8") as f_output:
                csv_output = csv.writer(f_output)
                csv_output.writerow(output_list)
        except Exception as e:
            logging.error(e)

def writeHeaderToCSV():
    header = [
        "Symbol",
        "Current Price",
        "Strike Price",
        "Delta",
        "Premium",
        "Shares",
        "Total Premium",
        "ROR",
        "Expiry Date",
        "DTE",
        "Annual ROR",
        "Capital",
        "Open Int"
    ]

    try:
        with open(parser['OUTPUT_FILE'], "w", newline="", encoding="utf-8") as f_output:
            csv_output = csv.writer(f_output)
            csv_output.writerow(header)
    except Exception as e:
        logging.error(e)


if __name__ == "__main__":
    df = pd.read_csv(parser['WATCHLIST'])
    tickers = df["Ticker"].to_list()
    writeHeaderToCSV()

    for idx, sym in tqdm(enumerate(tickers), total=len(tickers)):
        # print("{}: {}/{}".format(sym, idx, len(tickers)))
        WheelSellObj = WheelSell(sym)
        option_data = WheelSellObj.pullOptionChain()

        if not option_data:
            logging.info("{} skipped".format(sym))
            continue

        wheel = Wheeler(option_data)
        wheel.writeRowToCSV()
