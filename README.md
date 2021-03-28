# Stocks
This project uses Python and the yfinance library to populate a set of tables in a SQLite database with the price and quantity information for the holdings in an investment portfolio based on a given date and a ledger containing quantities of holdings that were either bought or sold and the date of each transaction.

## Steps
1. Populate the quotes table with daily stock quote information for each stock in the portfolio (excluding cash).
2. Populate the report_lines table with quantity and quote data for each holding with quantity > 0 in the portfolio as of the given date.
3. Populate the report_summary table with the quote data for the aggregated holdings in the stock portfolio for the given date.

## Project Database
This project uses an SQLite database contained in the file `stock_portfolio.sqlite`.
The database contains two tables that are already populated and are used as the source for loading the quotes, report_lines, and report_summary tables:

* The `stocks` table contains one record for each different stock symbol that is being tracked in the portfolio.
* The `portfolio` table contains one record for each trade and includes the quantity of shares that were either bought or sold, the date of the transaction, and the stock ID that was traded.

## Tables in the SQLite Database
`stocks` - the holdings in the portfolio for which price and quantity data is being tracked
* id (interger), name (text), symbol (text)

`quotes` - daily stock quote information for each stock in the portfolio (excluding cash)
* stock_id (integer), date (date), open (numeric), high (numeric), low (numeric), close(numeric)

`portfolio` - ledger of transactions in the portfolio
* stock_id (integer), date (date), quantity (numeric)

`report_lines` - quantity and quote data aggregated for each holding with quantity > 0 in the portfolio as of the given date
* date (date), stock_name (text), stock_symbol (text), quantity (numeric), open_value (numeric), high_value (numeric), low_value (numeric), close_value (numeric)

`report_summary` - quote data for all holdings in the entire stock portfolio aggregated for the given date
* date (date), open_value (numeric), high_value (numeric), low_value (numeric), close_value (numeric)


## Project Files
The project includes three files:

1. `storable.py` generates the quote data for the stock portfolio based on the given date and the holdings in the portfolio on that day.
2. `param.cfg` is a configuration file that contains the path to the SQLite database and a list of dates for which the quote data should be generated.
3. `stock_portfolio.sqlite` is an SQLite database file with all of the tables that are used in this project.

## Instructions

1. Edit `param.cfg` to include the path to the SQLite database file and a list of dates for which to generate the report. The dates can be given in YYYY-MM-DD format separated by commas. e.g. DATE=2020-10-01,2020-11-02,2020-12-01
3. Run `storable.py` along with the configuration file name passed as a command line argument. e.g. `python storable.py param.cfg`
