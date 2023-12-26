# wheel-option-chain
Repository to pull option data from TD Ameritrade and offers the options to buy for Wheeling Strategy.

## Project Directory
```
wheel-option-chain
├─ config
│  └─ config.sample.yaml
├─ output
│  └─ wheel.csv
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ main.py
│  ├─ pd_normalize.py
│  └─ sell_contract.py
└─ watchlist.sample.csv
```

## Steps to configure project
- Rename `config/config.sample.yaml` to `config/config.yaml`
- Update `TD_API_KEY` and `EXPIRYDATE`. Check expiry date according to official option chain data
- Update `PARAMS_OPTIONS.CONTRACT_TYPE` to either `PUT` or `CALL` depending on which contract type you want to pull
- Create a csv (e.g. `watchlist.csv`) to indicate all company tickers and update `WATCHLIST` in `config/config.yaml`

## How to run
```
pip install -r requirements.txt
python scripts/main.py
```
