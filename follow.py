import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from ttkthemes import ThemedTk
import json
import os
from datetime import datetime
import sqlite3
import re
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_follow_improved.log'),
        logging.StreamHandler()
    ]
)

class TwitterFollowBot:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.config = self.load_config()
        self.setup_database()
        self.setup_driver()

    def load_config(self):
        if os.path.exists('follow_config.json'):
            with open('follow_config.json', 'r') as f:
                return json.load(f)
        return {
            'delay_min': 3,
            'delay_max': 7,
            'max_follows_per_day': 200,
            'proxy_enabled': False,
            'proxies': [],
            'follow_ratio': 0.8,
            'max_followers': 5000,
            'max_following': 5000,
            'min_followers': 100,
            'min_following': 100,
            'max_retries': 3,
            'follow_delay': 5
        }

    def save_config(self):
        with open('follow_config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_database(self):
        self.conn = sqlite3.connect('twitter_follow.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                password TEXT,
                proxy TEXT,
                follows_today INTEGER DEFAULT 0,
                last_follow_date TEXT,
                total_follows INTEGER DEFAULT 0,
                last_activity TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS following (
                account_username TEXT,
                followed_username TEXT,
                follow_date TEXT,
                unfollow_date TEXT,
                FOREIGN KEY (account_username) REFERENCES accounts(username)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                username TEXT PRIMARY KEY,
                followers_count INTEGER,
                following_count INTEGER,
                last_updated TEXT
            )
        ''')
        self.conn.commit()

    def setup_driver(self):
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        if self.config['proxy_enabled'] and self.config['proxies']:
            proxy = random.choice(self.config['proxies'])
            options.add_argument(f'--proxy-server={proxy}')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def login(self, username, password):
        try:
            self.driver.get("https://twitter.com/i/flow/login")
            wait = WebDriverWait(self.driver, 30)

            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
            username_field.send_keys(username)
            time.sleep(random.uniform(1, 2))
            
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[role="button"].r-13qz1uu')))
            next_button.click()
            time.sleep(random.uniform(1, 2))

            password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
            password_field.send_keys(password)
            time.sleep(random.uniform(1, 2))
            
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="LoginForm_Login_Button"]')))
            login_button.click()

            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
            logging.info(f"Successfully logged in as {username}")
            return True
        except Exception as e:
            logging.error(f"Login failed for {username}: {str(e)}")
            return False

    def can_follow_more(self, username):
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            SELECT follows_today, last_follow_date, total_follows 
            FROM accounts 
            WHERE username = ?
        ''', (username,))
        result = self.cursor.fetchone()
        
        if result:
            follows_today, last_follow_date, total_follows = result
            if last_follow_date != today:
                self.cursor.execute('''
                    UPDATE accounts 
                    SET follows_today = 0, last_follow_date = ? 
                    WHERE username = ?
                ''', (today, username))
                self.conn.commit()
                return True
            return follows_today < self.config['max_follows_per_day'] and total_follows < self.config['max_following']
        return True

    def update_follow_count(self, username):
        today = datetime.now().strftime('%Y-%m-%d')
        self.cursor.execute('''
            UPDATE accounts 
            SET follows_today = follows_today + 1, 
                last_follow_date = ?,
                total_follows = total_follows + 1,
                last_activity = ?
            WHERE username = ?
        ''', (today, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username))
        self.conn.commit()

    def get_user_stats(self, username):
        try:
            self.driver.get(f"https://twitter.com/{username}")
            wait = WebDriverWait(self.driver, 30)
            
            followers_count = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[href$="/followers"] span'))).text
            following_count = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[href$="/following"] span'))).text
            
            stats = {
                'followers': int(followers_count.replace(',', '')),
                'following': int(following_count.replace(',', ''))
            }
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO user_stats (username, followers_count, following_count, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (username, stats['followers'], stats['following'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            
            return stats
        except Exception as e:
            logging.error(f"Failed to get stats for {username}: {str(e)}")
            return None

    def is_valid_target(self, username):
        stats = self.get_user_stats(username)
        if not stats:
            return False
            
        return (
            stats['followers'] >= self.config['min_followers'] and
            stats['followers'] <= self.config['max_followers'] and
            stats['following'] >= self.config['min_following'] and
            stats['following'] <= self.config['max_following'] and
            stats['following'] / max(stats['followers'], 1) <= self.config['follow_ratio']
        )

    def follow_user(self, username, target_username):
        try:
            if not self.can_follow_more(username):
                logging.warning(f"Account {username} has reached follow limits")
                return False

            if not self.is_valid_target(target_username):
                logging.warning(f"Target {target_username} doesn't meet criteria")
                return False

            self.driver.get(f"https://twitter.com/{target_username}")
            wait = WebDriverWait(self.driver, 30)
            
            follow_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="followButton"]')))
            follow_button.click()
            time.sleep(random.uniform(self.config['follow_delay'], self.config['follow_delay'] + 2))

            today = datetime.now().strftime('%Y-%m-%d')
            self.update_follow_count(username)
            
            self.cursor.execute('''
                INSERT INTO following (account_username, followed_username, follow_date)
                VALUES (?, ?, ?)
            ''', (username, target_username, today))
            
            self.conn.commit()
            logging.info(f"Account {username} followed {target_username}")
            return True
        except Exception as e:
            logging.error(f"Failed to follow {target_username}: {str(e)}")
            return False

    def unfollow_user(self, username, target_username):
        try:
            self.driver.get(f"https://twitter.com/{target_username}")
            wait = WebDriverWait(self.driver, 30)
            
            unfollow_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="unfollow"]')))
            unfollow_button.click()
            time.sleep(random.uniform(1, 2))
            
            confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="confirmationSheetConfirm"]')))
            confirm_button.click()
            time.sleep(random.uniform(1, 2))

            self.cursor.execute('''
                UPDATE following 
                SET unfollow_date = ? 
                WHERE account_username = ? AND followed_username = ? AND unfollow_date IS NULL
            ''', (datetime.now().strftime('%Y-%m-%d'), username, target_username))
            self.conn.commit()
            
            logging.info(f"Account {username} unfollowed {target_username}")
            return True
        except Exception as e:
            logging.error(f"Failed to unfollow {target_username}: {str(e)}")
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
        if self.conn:
            self.conn.close()

class TwitterFollowGUI(ThemedTk):
    def __init__(self):
        super().__init__()
        self.title("Twitter Follow Bot (Improved)")
        self.geometry("800x600")
        self.set_theme("arc")
        
        self.bot = TwitterFollowBot()
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.analytics_tab = ttk.Frame(self.notebook)
        self.unfollow_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.analytics_tab, text="Analytics")
        self.notebook.add(self.unfollow_tab, text="Unfollow")

        self.create_main_tab()
        self.create_settings_tab()
        self.create_analytics_tab()
        self.create_unfollow_tab()

    def create_main_tab(self):
        # Accounts section
        ttk.Label(self.main_tab, text="Accounts (username:password):").pack(pady=5)
        self.accounts_text = tk.Text(self.main_tab, height=5)
        self.accounts_text.pack(fill=tk.X, padx=5)

        # Target users section
        ttk.Label(self.main_tab, text="Target Users:").pack(pady=5)
        self.targets_text = tk.Text(self.main_tab, height=5)
        self.targets_text.pack(fill=tk.X, padx=5)

        # Threads entry
        ttk.Label(self.main_tab, text="Number of Threads:").pack(pady=5)
        self.threads_entry = ttk.Entry(self.main_tab)
        self.threads_entry.pack()

        # Start button
        ttk.Button(self.main_tab, text="Start Following", command=self.start_following).pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self.main_tab, text="Status: Ready")
        self.status_label.pack()

    def create_settings_tab(self):
        # Delay settings
        ttk.Label(self.settings_tab, text="Minimum Delay (seconds):").pack(pady=5)
        self.min_delay_entry = ttk.Entry(self.settings_tab)
        self.min_delay_entry.pack()
        self.min_delay_entry.insert(0, str(self.bot.config['delay_min']))

        ttk.Label(self.settings_tab, text="Maximum Delay (seconds):").pack(pady=5)
        self.max_delay_entry = ttk.Entry(self.settings_tab)
        self.max_delay_entry.pack()
        self.max_delay_entry.insert(0, str(self.bot.config['delay_max']))

        # Follow limits
        ttk.Label(self.settings_tab, text="Max Follows Per Day:").pack(pady=5)
        self.max_follows_entry = ttk.Entry(self.settings_tab)
        self.max_follows_entry.pack()
        self.max_follows_entry.insert(0, str(self.bot.config['max_follows_per_day']))

        # Follow ratio
        ttk.Label(self.settings_tab, text="Max Follow Ratio:").pack(pady=5)
        self.follow_ratio_entry = ttk.Entry(self.settings_tab)
        self.follow_ratio_entry.pack()
        self.follow_ratio_entry.insert(0, str(self.bot.config['follow_ratio']))

        # Follower limits
        ttk.Label(self.settings_tab, text="Min Followers:").pack(pady=5)
        self.min_followers_entry = ttk.Entry(self.settings_tab)
        self.min_followers_entry.pack()
        self.min_followers_entry.insert(0, str(self.bot.config['min_followers']))

        ttk.Label(self.settings_tab, text="Max Followers:").pack(pady=5)
        self.max_followers_entry = ttk.Entry(self.settings_tab)
        self.max_followers_entry.pack()
        self.max_followers_entry.insert(0, str(self.bot.config['max_followers']))

        # Following limits
        ttk.Label(self.settings_tab, text="Min Following:").pack(pady=5)
        self.min_following_entry = ttk.Entry(self.settings_tab)
        self.min_following_entry.pack()
        self.min_following_entry.insert(0, str(self.bot.config['min_following']))

        ttk.Label(self.settings_tab, text="Max Following:").pack(pady=5)
        self.max_following_entry = ttk.Entry(self.settings_tab)
        self.max_following_entry.pack()
        self.max_following_entry.insert(0, str(self.bot.config['max_following']))

        # Proxy settings
        self.proxy_var = tk.BooleanVar(value=self.bot.config['proxy_enabled'])
        ttk.Checkbutton(self.settings_tab, text="Enable Proxies", variable=self.proxy_var).pack(pady=5)

        ttk.Label(self.settings_tab, text="Proxies (ip:port:username:password):").pack(pady=5)
        self.proxies_text = tk.Text(self.settings_tab, height=5)
        self.proxies_text.pack(fill=tk.X, padx=5)
        for proxy in self.bot.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

        # Save settings button
        ttk.Button(self.settings_tab, text="Save Settings", command=self.save_settings).pack(pady=10)

    def create_analytics_tab(self):
        # Follow statistics
        ttk.Label(self.analytics_tab, text="Follow Statistics:").pack(pady=5)
        self.stats_text = tk.Text(self.analytics_tab, height=10)
        self.stats_text.pack(fill=tk.X, padx=5)

        # Refresh button
        ttk.Button(self.analytics_tab, text="Refresh Statistics", command=self.refresh_stats).pack(pady=10)

    def create_unfollow_tab(self):
        # Accounts section
        ttk.Label(self.unfollow_tab, text="Accounts (username:password):").pack(pady=5)
        self.unfollow_accounts_text = tk.Text(self.unfollow_tab, height=5)
        self.unfollow_accounts_text.pack(fill=tk.X, padx=5)

        # Target users section
        ttk.Label(self.unfollow_tab, text="Users to Unfollow:").pack(pady=5)
        self.unfollow_targets_text = tk.Text(self.unfollow_tab, height=5)
        self.unfollow_targets_text.pack(fill=tk.X, padx=5)

        # Threads entry
        ttk.Label(self.unfollow_tab, text="Number of Threads:").pack(pady=5)
        self.unfollow_threads_entry = ttk.Entry(self.unfollow_tab)
        self.unfollow_threads_entry.pack()

        # Start button
        ttk.Button(self.unfollow_tab, text="Start Unfollowing", command=self.start_unfollowing).pack(pady=10)

        # Status label
        self.unfollow_status_label = ttk.Label(self.unfollow_tab, text="Status: Ready")
        self.unfollow_status_label.pack()

    def load_config(self):
        self.min_delay_entry.delete(0, tk.END)
        self.min_delay_entry.insert(0, str(self.bot.config['delay_min']))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(self.bot.config['delay_max']))
        self.max_follows_entry.delete(0, tk.END)
        self.max_follows_entry.insert(0, str(self.bot.config['max_follows_per_day']))
        self.follow_ratio_entry.delete(0, tk.END)
        self.follow_ratio_entry.insert(0, str(self.bot.config['follow_ratio']))
        self.min_followers_entry.delete(0, tk.END)
        self.min_followers_entry.insert(0, str(self.bot.config['min_followers']))
        self.max_followers_entry.delete(0, tk.END)
        self.max_followers_entry.insert(0, str(self.bot.config['max_followers']))
        self.min_following_entry.delete(0, tk.END)
        self.min_following_entry.insert(0, str(self.bot.config['min_following']))
        self.max_following_entry.delete(0, tk.END)
        self.max_following_entry.insert(0, str(self.bot.config['max_following']))
        self.proxy_var.set(self.bot.config['proxy_enabled'])
        self.proxies_text.delete(1.0, tk.END)
        for proxy in self.bot.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

    def save_settings(self):
        try:
            self.bot.config['delay_min'] = float(self.min_delay_entry.get())
            self.bot.config['delay_max'] = float(self.max_delay_entry.get())
            self.bot.config['max_follows_per_day'] = int(self.max_follows_entry.get())
            self.bot.config['follow_ratio'] = float(self.follow_ratio_entry.get())
            self.bot.config['min_followers'] = int(self.min_followers_entry.get())
            self.bot.config['max_followers'] = int(self.max_followers_entry.get())
            self.bot.config['min_following'] = int(self.min_following_entry.get())
            self.bot.config['max_following'] = int(self.max_following_entry.get())
            self.bot.config['proxy_enabled'] = self.proxy_var.get()
            self.bot.config['proxies'] = [line.strip() for line in self.proxies_text.get(1.0, tk.END).split('\n') if line.strip()]
            self.bot.save_config()
            messagebox.showinfo("Success", "Settings saved successfully")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def refresh_stats(self):
        self.bot.cursor.execute('''
            SELECT account_username, COUNT(*) as follows_count, MAX(follow_date) as last_follow
            FROM following
            WHERE unfollow_date IS NULL
            GROUP BY account_username
        ''')
        stats = self.bot.cursor.fetchall()
        
        self.stats_text.delete(1.0, tk.END)
        for stat in stats:
            self.stats_text.insert(tk.END, f"Account: {stat[0]}\n")
            self.stats_text.insert(tk.END, f"Total Follows: {stat[1]}\n")
            self.stats_text.insert(tk.END, f"Last Follow: {stat[2]}\n\n")

    def start_following(self):
        if self.bot.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return

        accounts = [line.strip().split(":") for line in self.accounts_text.get(1.0, tk.END).split('\n') if ":" in line]
        targets = [line.strip() for line in self.targets_text.get(1.0, tk.END).split('\n') if line.strip()]
        threads = int(self.threads_entry.get() or 1)

        if not accounts or not targets:
            messagebox.showerror("Error", "Please fill all required fields")
            return

        self.bot.is_running = True
        self.status_label.config(text="Status: Running")
        
        threading.Thread(target=self.run_following, args=(accounts, targets, threads)).start()

    def run_following(self, accounts, targets, threads):
        def worker(account):
            bot = TwitterFollowBot()
            try:
                if bot.login(account[0], account[1]):
                    for target in targets:
                        if not self.bot.is_running:
                            break
                        bot.follow_user(account[0], target)
            finally:
                bot.close()

        active_threads = []
        for account in accounts:
            if not self.bot.is_running:
                break
                
            if len(active_threads) >= threads:
                for t in active_threads:
                    t.join()
                active_threads = []

            t = threading.Thread(target=worker, args=(account,))
            t.start()
            active_threads.append(t)

        for t in active_threads:
            t.join()

        self.bot.is_running = False
        self.status_label.config(text="Status: Completed")
        messagebox.showinfo("Info", "Following completed")
        self.refresh_stats()

    def start_unfollowing(self):
        if self.bot.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return

        accounts = [line.strip().split(":") for line in self.unfollow_accounts_text.get(1.0, tk.END).split('\n') if ":" in line]
        targets = [line.strip() for line in self.unfollow_targets_text.get(1.0, tk.END).split('\n') if line.strip()]
        threads = int(self.unfollow_threads_entry.get() or 1)

        if not accounts or not targets:
            messagebox.showerror("Error", "Please fill all required fields")
            return

        self.bot.is_running = True
        self.unfollow_status_label.config(text="Status: Running")
        
        threading.Thread(target=self.run_unfollowing, args=(accounts, targets, threads)).start()

    def run_unfollowing(self, accounts, targets, threads):
        def worker(account):
            bot = TwitterFollowBot()
            try:
                if bot.login(account[0], account[1]):
                    for target in targets:
                        if not self.bot.is_running:
                            break
                        bot.unfollow_user(account[0], target)
            finally:
                bot.close()

        active_threads = []
        for account in accounts:
            if not self.bot.is_running:
                break
                
            if len(active_threads) >= threads:
                for t in active_threads:
                    t.join()
                active_threads = []

            t = threading.Thread(target=worker, args=(account,))
            t.start()
            active_threads.append(t)

        for t in active_threads:
            t.join()

        self.bot.is_running = False
        self.unfollow_status_label.config(text="Status: Completed")
        messagebox.showinfo("Info", "Unfollowing completed")
        self.refresh_stats()

if __name__ == "__main__":
    app = TwitterFollowGUI()
    app.mainloop() 
