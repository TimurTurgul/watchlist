from bs4 import BeautifulSoup
import sqlite3
import requests

def setup_table():
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'")
    table_exists = cur.fetchone()
    if not table_exists:
        cur.execute("CREATE TABLE watchlist (id INTEGER PRIMARY KEY UNIQUE, url TEXT UNIQUE, title TEXT, min_price REAL, current_price REAL, max_price REAL)")
        conn.commit()

def duplicate_check(url): #either returns the url or "None"
    cur.execute("SELECT url FROM watchlist WHERE url= ?", (url,))
    duplicate = cur.fetchone()
    return duplicate

def scrape(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        title = str(soup.find("meta", {"property": "og:title"})["content"].strip())
        price = float(soup.find("meta", {"property": "product:price:amount"})["content"].strip())
    except: return
    return (title, price)

def add_product(url, title, price):
    cur.execute("INSERT INTO watchlist (url, title, min_price, current_price, max_price) VALUES (?, ?, ?, ?, ?)", (url, title, price, price, price))
    conn.commit()
    print(f"\n>>> Product: {title}, price: {price} CHF successfully added to your watchlist!")

def new_url():
    url = input("\n>>> Enter new product URL:\n").strip()
    duplicate = duplicate_check(url)
    
    if duplicate: #is truthy if the check didn't return "None as value"
        print("\n>>> This URL is already on your watchlist.")
        return
    
    try: # title might be None
        title, price = scrape(url)
    except: 
        print("\n>>> Error: Invalid URL.")
        return

    while True:
        qadd = input(f"\n>>> Do you wish to add product: {title}, price: {price} CHF to your watchlist? [y/n]:\n")
        if qadd == "n":
            print("\n>>> Product has NOT been added!")
            break
        elif qadd == "y":
            add_product(url, title, price)
            break
        
def update_price(id, url, title):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        new_price = float(soup.find("meta", {"property": "product:price:amount"})["content"].strip())
        return new_price
    except:
        return False
    

def corrupted_url(id, title):
    print(f"\n>>> Error: Couldn't update the price for: {title}")
    print(">>> The product is no longer listed on the website or it's URL changed")
    while True:
        qrem = input(f">>> Would you like to remove the product from the watchlist. Please confirm [y/n]:\n")
        if qrem == "n":
            print(f"\n>>> Product has not been removed.")
            print(">>> Continuing the update...")
            break
        elif qrem == "y":
            cur.execute("DELETE FROM watchlist WHERE id = ?", (id,))
            conn.commit()
            print(f"\n>>> Product has been successfully removed from watchlist!")
            print(">>> Continuing the update...")
            break
    return

def update_watchlist():
    while True:
        qupdate = input("\n>>> This might take a while. Do you wish to update your watchlist now? [y/n]:\n")
        if qupdate == "n":
            print("\n>>> Your watchlist has NOT been updated!")
            break
        
        elif qupdate == "y":
            cur.execute("SELECT * FROM watchlist")
            rows = cur.fetchall()
            if not rows:
                print("\n>>> Your watchlist is empty. There is nothing to update")
                return
            update_message = ""
            for row in rows:
                id, url, title, min_price, current_price, max_price = row
                new_price = update_price(id, url, title)
               
                if not new_price:  # new_price could be None
                    corrupted_url(id, title)
                    continue
                
                if new_price != current_price:
                    cur.execute("UPDATE watchlist SET current_price = ? WHERE id = ?", (new_price, id))
                    minmax = ""
                    if new_price < min_price:
                        cur.execute("UPDATE watchlist SET min_price = ? WHERE id = ?", (new_price, id))
                        minmax = " The price is currently at a new all-time low!"
                    elif new_price > max_price:
                        cur.execute("UPDATE watchlist SET max_price = ? WHERE id = ?", (new_price, id))
                        minmax = " The price is currently at a new all-time high!"
                        
                    update_message += f"\n>>> The price for {title} has changed from {current_price} CHF to {new_price} CHF.{minmax}"
            
            conn.commit()
            print("\n>>> Your watchlist has been successfully updated!")
            
            if not update_message:
                print(">>> There have been no changes.")
                return
            else:
                while True:
                    qreport = input(">>> There have been changes. Would you like to see an update report? [y/n]:\n")
                    if qreport == "y": print(update_message); return
                    elif qreport == "n": return

def print_watchlist():
        cur.execute("SELECT title, current_price FROM watchlist")
        rows = cur.fetchall()
        
        if not rows:
            print("\n>>> Your watchlist is empty.")
            return
        
        print("")
        for row in rows:
            title, current_price = row
            print(f">>> {title} | {current_price} CHF")

def remove_product():
    cur.execute("SELECT id, title, current_price FROM watchlist")
    rows = cur.fetchall()
    
    if not rows:
        print("\n>>> Your watchlist is empty.")
        return
    
    ids = []
    print("")
    for row in rows:
        id, title, current_price = row
        ids.append(str(id))
        print(f"[{id}]: {title} | {current_price} CHF")

    while True:
        id = input("\n>>> Which product do you wish to remove? Enter the corresponding ID number or 'x' to exit:\n")
        
        if id == "x":
            print("\n>>> Product has not been removed.")
            break

        elif id in ids:
            cur.execute("SELECT id, title FROM watchlist WHERE id = ?", (id,))
            title = cur.fetchone()
            while True:
                qrem = input(f"\n>>> Removing {title} from the watchlist. Please confirm [y/n]:\n")
                if qrem == "n":
                    print("\n>>> No product has been removed.")
                    return
                elif qrem == "y":
                    cur.execute("DELETE FROM watchlist WHERE id = ?", (id,))
                    conn.commit()
                    print(f"\n>>> {title} has been successfully removed from watchlist!")
                    return
        else:
            print("\n>>> Invalid ID.")            


conn = sqlite3.connect("watchlistdb.sqlite3")
cur = conn.cursor()
setup_table()

while True:
    task = input("""\n>>> What do you wish to do? Enter the corresponding number:
    1) Add a new product to the watchlist
    2) Update prices
    3) Print watchlist
    4) Remove a product from the watchlist
    5) Exit the program\n""")
        
    if task == "1": new_url()
    elif task == "2": update_watchlist()
    elif task == "3": print_watchlist()
    elif task == "4": remove_product()
    elif task == "5": break

cur.close()
conn.close()