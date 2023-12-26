import logging
from pd_normalize import normalize
import yaml
import datetime
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas as pd
from dateutil.relativedelta import relativedelta

logging.basicConfig(level="ERROR")

with open("config/config.yaml", "r") as stream:
    try:
        parser = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        logging.error(e)


class WheelSell:
    def __init__(self, symbol):
        self.apikey = parser["TD"]["TD_API_KEY"]
        self.symbol = symbol
        self.contractType = parser["PARAMS_OPTIONS"]["CONTRACT_TYPE"]
        self.fromDate = ""
        self.toDate = ""
        self.optionType = parser["PARAMS_OPTIONS"]["OPTION_TYPE"]
        self.payload = {}
        self.optionChainDF = None

        # Parameters for buy calls
        self.delta = parser["PARAMS_OPTIONS"]["DELTA"]
        self.deltaDev = parser["PARAMS_OPTIONS"]["DELTADEV"]
        self.openInterest = parser["PARAMS_OPTIONS"]["OPEN_INTEREST"]
        self.numContracts = parser["PARAMS_OPTIONS"]["NUM_CONTRACTS"]

        # After pulling data
        self.data = {}
        self.mktPrice = 0
        self.expiryDate = parser["EXPIRYDATE"]
        self.premium = 0
        self.strikeprice = 0
        self.actualDelta = 0
        self.open_int = 0

        self.getFromToDate()
        self.initPayload()

    def getFromToDate(self):
        expiryDate = datetime.datetime.strptime(self.expiryDate, "%Y-%m-%d").date()
        self.fromDate = expiryDate - relativedelta(days=1)
        self.toDate = expiryDate + relativedelta(days=1)

    def calculateDTE(self):
        expiryDate = datetime.datetime.strptime(self.expiryDate, "%Y-%m-%d").date()
        return (expiryDate - datetime.date.today()).days

    def initPayload(self):
        self.payload = {
            "apikey": self.apikey,
            "symbol": self.symbol,
            "contractType": self.contractType,
            "fromDate": self.fromDate,
            "toDate": self.toDate,
            "optionType": self.optionType,
        }

    def getOptionChain(self):
        # Check for contract type (PUT vs CALL)
        if self.contractType == "PUT":
            optionChain = self.data["putExpDateMap"].values()
        elif self.contractType == "CALL":
            optionChain = self.data["callExpDateMap"].values()

        optionChainDF = pd.json_normalize(optionChain).melt(
            var_name="Option Price", value_name="Values"
        )
        optionChainDF = normalize(optionChainDF)
        optionChainDF = optionChainDF[
            [
                "Values.strikePrice",
                "Values.bid",
                "Values.ask",
                "Values.delta",
                "Values.openInterest",
            ]
        ]
        optionChainDF = optionChainDF[optionChainDF["Values.delta"] != "NaN"]
        self.optionChainDF = optionChainDF

        return

    def filterOptionChain(self):
        # Check for delta close to 0.3
        df = self.optionChainDF[
            abs(abs(self.optionChainDF["Values.delta"]) - self.delta) <= self.deltaDev
        ]
        # Check for Open Interest
        df = df[df["Values.openInterest"] >= self.openInterest]
        # Get the lowest premium + Strike Price
        df["Premium"] = df["Values.ask"] * 100

        if df.empty:
            return False

        self.premium = (df["Values.bid"].iloc[0] + df["Values.ask"].iloc[0])/2.0
        self.strikeprice = df["Values.strikePrice"].iloc[0]
        self.actualDelta = df["Values.delta"].iloc[0]
        self.open_int = df["Values.openInterest"].iloc[0]

        return True

    def pullOptionChain(self):
        session = requests.Session()
        retry = Retry(
            connect=parser["SSL"]["RETRIES"],
            backoff_factor=parser["SSL"]["BACKOFF_FACTOR"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)

        try:
            r = session.get(parser["TD"]["TD_RESOURCE_URL"], params=self.payload)

            data = r.json()
            self.data = data

            # Get Mkt Price
            self.mktPrice = self.data["underlyingPrice"]

            # Get Buy Call Strike Price
            self.getOptionChain()
            if not self.filterOptionChain():
                return False

            dte = self.calculateDTE()
            ror = (self.premium * self.numContracts * 100) / (self.strikeprice * self.numContracts * 100) * 100.0
            capital = self.strikeprice * self.numContracts * 100
            annual_ror = ror / dte * 365

            return {
                "symbol": self.symbol,
                "mktPrice": self.mktPrice,
                "strikeprice": self.strikeprice,
                "actualDelta": self.actualDelta,
                "premium": self.premium,
                "numshares": self.numContracts * 100,
                "expirydate": self.expiryDate,
                "dte": dte,
                "ror": ror,
                "annual_ror": annual_ror,
                "capital": capital,
                "open_int": self.open_int
            }

        except Exception as e:
            logging.error(e)
