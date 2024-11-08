from flask import Flask, jsonify, render_template, request
import sqlite3
from contextlib import contextmanager
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('stocks1.db')
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Fetch all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row['name'] for row in cursor.fetchall()]
            
            if not tables:
                return "No tables found in the database", 404
            
            # Fetch stocks from the first table (or a default table)
            default_table = tables[0]
            cursor.execute(f"SELECT Stock_name as name, Symbol as symbol FROM {default_table} ORDER BY Stock_name")
            stocks = [dict(row) for row in cursor.fetchall()]
            
            return render_template('index.html', tables=tables, stocks=stocks)
    except sqlite3.Error as e:
        app.logger.error(f"SQLite error: {e}")
        return f"Database error: {str(e)}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return f"An unexpected error occurred: {str(e)}", 500

@app.route('/get_stocks')
def get_stocks():
    try:
        table_name = request.args.get('table')
        if not table_name:
            return jsonify({'error': 'Table name is required'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT Stock_name as name, Symbol as symbol FROM {table_name} ORDER BY Stock_name")
            stocks = [dict(row) for row in cursor.fetchall()]
        return jsonify(stocks)
    except sqlite3.Error as e:
        app.logger.error(f"SQLite error: {e}")
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/get_stock_data')
def get_stock_data():
    try:
        symbol = request.args.get('symbol', '')
        if not symbol:
            return jsonify({'error': 'Symbol is required'}), 400
        
        yf_symbol = f"{symbol}.NS"
        stock = yf.Ticker(yf_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        df = stock.history(period='6mo', interval='1d')
        
        chart_data = [
            {
                'time': index.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume']),
            }
            for index, row in df.iterrows()
        ]
        
        return jsonify(chart_data)
    except Exception as e:
        app.logger.error(f"Error fetching stock data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
