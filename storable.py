import sqlite3
from sqlite3 import Error
import yfinance as yf
from datetime import date
from datetime import datetime
from datetime import timedelta
import configparser
import sys

def create_connection(db_file):
    """ 
    Creates a database connection to the SQLite database
    specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def update_quotes(conn,start_date,end_date):
    """
    Populates the quotes table with the daily price information for the given date.
    :param conn: the Connection object
    :param start_date: the date for which we want to generate the portfolio summary
    :param end_date: one day after the start date
    :return:
    """
    # Selecting all stock IDs and ticker symbols from the stocks table, excluding cash
    
    cur = conn.cursor()
    cur.execute("SELECT id,symbol FROM stocks WHERE symbol != '$$$$'")
    
    holdings = cur.fetchall()
    
    # For each stock holding in the portfolio
    
    for holding in holdings:

        # Using yfinance library, fetch the Open, High, Low, and Close values for the specified date
        # and ticker symbol
        
        ticker = yf.Ticker(holding[1])
        data = ticker.history(start=start_date, end=end_date, auto_adjust=False)
        
        if len(data) == 0:
            continue
        
        # Inserting the daily quote information into the quotes table
        
        insert_values = (start_date.date(), 
                         holding[0], 
                         round(float(data['Open']),2), 
                         round(float(data['High']),2),
                         round(float(data['Low']),2),
                         round(float(data['Close']),2))

        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_quotes_date_id ON quotes(date,stock_id)")
        conn.commit()
        cur.execute("""INSERT OR REPLACE INTO quotes (
                            date, 
                            stock_id, 
                            open, 
                            high, 
                            low, 
                            close)
                        VALUES(?, ?, ?, ?, ?, ?)""", insert_values)
        conn.commit()
    
    # Deleting and reinserting the data to order by stock ID and date
    
    cur.execute("""SELECT
                        date, 
                        stock_id, 
                        open, 
                        high, 
                        low, 
                        close 
                   FROM quotes ORDER BY stock_id, date""")
    results = cur.fetchall()
    
    cur.execute("DELETE FROM quotes")
    conn.commit()
    
    for row in results:

        insert_values = (row[0], 
                         row[1], 
                         row[2],
                         row[3],
                         row[4],
                         row[5])
        
        cur.execute("""INSERT INTO quotes (
                            date, 
                            stock_id, 
                            open, 
                            high, 
                            low, 
                            close)
                        VALUES(?, ?, ?, ?, ?, ?)""", insert_values)
        conn.commit()
    
    # Verifying that records have been inserted for the specified date
    
    cur.execute("""SELECT COUNT(1) FROM quotes WHERE date = ?""",(start_date.date(),))
    count = cur.fetchall()[0][0]
    
    if count == 0:
        print("ERROR: No records have been inserted into the quotes table for date{}.".format(count))
    else:            
        print("{} records have been inserted into quotes table for date {}.".format(count,start_date.date()))
        
def update_report_lines(conn,start_date,end_date):
    """
    Populates the report_lines table with the aggregated quantity and price data for each holding in the
    portfolio for the given date.
    :param conn: the Connection object
    :param start_date: the date for which we want to generate the portfolio summary
    :param end_date: one day after the start date
    :return:
    """
    # Selecting the quanitity of each holding in the portfolio (including cash) on the report_date by 
    # summing the quantity changes for each holding due to all transactions that occured up to and 
    # including the report_date
        
    cur = conn.cursor()
    cur.execute("""SELECT 
                        s.symbol,
                        s.name,
                        sum(p.quantity) as quantity 
                    FROM portfolio p 
                    INNER JOIN stocks s 
                        ON p.stock_id = s.id 
                    WHERE date <= ?
                    GROUP BY s.symbol,s.name
                        HAVING sum(p.quantity) > 0
                    ORDER BY s.name asc""",(start_date.date(),))

    stock_symbol_quantities = cur.fetchall()

    # For each holding in the portfolio with a quantity > 0
    
    for row in stock_symbol_quantities:
        
        stock_symbol = row[0]
        stock_name = row[1]
        quantity = row[2]
        
        # If cash, set the Open, High, Low, and Close values equal to the quantity of cash in the
        # portfolio on the report_date and insert into the report_lines table.
        
        if stock_symbol == '$$$$':
            insert_values = (start_date.date(),
                             stock_name,
                             stock_symbol,
                             quantity,
                             quantity, 
                             quantity,
                             quantity,
                             quantity)
            
        # Otherwise, use yfinance library to fetch the Open, High, Low, and Close values for the specified date
        # and ticker symbol. Multiply these values by the number of shares of the holding contained in the 
        # portfolio to get the total Open, High, Low, and Close values for all combined shares of each 
        # holding on the report_date
            
        else:
            ticker = yf.Ticker(stock_symbol)
            data = ticker.history(start=start_date, end=end_date, auto_adjust=False)
            
            if len(data) == 0:
                continue
            
            insert_values = (start_date.date(),
                             stock_name,
                             stock_symbol,
                             quantity,
                             round(float(data['Open']) * quantity,2), 
                             round(float(data['High']) * quantity,2),
                             round(float(data['Low']) * quantity,2),
                             round(float(data['Close']) * quantity,2))
        
        cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_report_lines_date_symbol ON report_lines(date,stock_symbol)""")
        conn.commit()
        cur.execute("""INSERT OR REPLACE INTO report_lines (
                            date, 
                            stock_name, 
                            stock_symbol, 
                            quantity,
                            open_value,
                            high_value, 
                            low_value, 
                            close_value)
                        VALUES(?, ?, ?, ?, ?, ?, ?, ?)""", insert_values)
        conn.commit()
        
    # Verifying that records have been inserted for the specified date    
        
    cur.execute("""SELECT COUNT(1) FROM report_lines WHERE date = ?""",(start_date.date(),))
    count = cur.fetchall()[0][0]
        
    if count == 0:
        print("ERROR: No records have been inserted into the report_lines table for date{}.".format(count))
    else:            
        print("{} records have been inserted into report_lines table for date {}.".format(count,start_date.date()))
        
def update_report_summary(conn,start_date):
    """
    Populating the report_summary table with the price data for the aggregated holdings in
    the stock portfolio for the given date.
    :param start_date: the date for which we want to generate the portfolio summary
    :param conn: the Connection object
    :return:
    """
    # Selecting the total aggregated open_value, high_value, low_value, close_value 
    # from the report_lines table for all holdings in the portfolio on the specified date
    
    cur = conn.cursor()
    cur.execute("""SELECT ?,
                        sum(open_value) as open_value,
                        sum(high_value) as high_value,
                        sum(low_value) as low_value,
                        sum(close_value) as close_value 
                    FROM report_lines
                    WHERE date = ?""",(start_date.date(),start_date.date()))

    rows = cur.fetchall()
    
    # Insert the the aggregated open, high, low, and close values for the entire portfolio on the
    # specified day into the report_summary table
        
    open_value = rows[0][1]
    high_value = rows[0][2]
    low_value = rows[0][3]
    close_value = rows[0][4]
    
    insert_values = (start_date.date(),
                     open_value,
                     high_value,
                     low_value,
                     close_value)
    
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_report_summary_date ON report_summary(date)""")
    conn.commit()
    cur.execute("""INSERT OR REPLACE INTO report_summary (
                        date, 
                        open_value, 
                        high_value, 
                        low_value, 
                        close_value)
                    VALUES(?, ?, ?, ?, ?)""",insert_values)
    conn.commit()
    
    # Verifying that records have been inserted for the specified date
        
    cur.execute("""SELECT COUNT(1) FROM report_summary WHERE date = ?""",(start_date.date(),))
    count = cur.fetchall()[0][0]
        
    if count == 0:
        print("ERROR: No records have been inserted into the report_summary table for date {}.".format(count))
    else:            
        print("{} records have been inserted into report_summary table for date {}.".format(count,start_date.date()))
        
def daily_portfolio_summary(report_date, db_file):
    """
    Generates the daily investment portfolio summary data based on a specified date and inserts the data
    into the quotes, report_lines, and report_summary tables.
    :param report_date: the date for which we want to generate the portfolio summary
    :param db_file: database file
    :return:
    """
    # Setting the date range for which we want to fetch history data
    # start_date is the report_date
    # end date is one day after the report_date
    
    start_date = datetime.strptime(report_date, "%Y-%m-%d")
    end_date = start_date + timedelta(days=1)
    
    # Checking if the report_date is a valid trading day
    
    ticker = yf.Ticker('KO')
    data = ticker.history(start=start_date, end=end_date, auto_adjust=False)
    
    if len(data) == 0:
        print("ERROR: The date provided ({}) is not a valid trading day.".format(report_date))
        return
        
    # Creating a connection to the database
    conn = create_connection(db_file)
    
    # Populating the quotes table with the daily quote information for all holdings in the portfolio
    # (except cash) for the given date.
    update_quotes(conn,start_date,end_date)

    # Populating the report_lines table with quanitity and quote data for each holding with quantity > 0 
    # in the portfolio based on the given date
    update_report_lines(conn,start_date,end_date)

    # Populating the report_sumary table with the quote data for the aggregated holdings in
    # the stock portfolio for the given date
    update_report_summary(conn,start_date)

    conn.close()


def main():
    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    
    db_file = config['PARAMETERS']['DB_PATH']
    report_dates = config['PARAMETERS']['DATES']
    
    # Storing the report dates in a list
    report_dates = report_dates.split(',')
    
    for date in report_dates:
        daily_portfolio_summary(date,db_file)


if __name__ == "__main__":
    main()
