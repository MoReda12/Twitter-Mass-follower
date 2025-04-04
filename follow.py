import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import random

class TwitterFollowBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitter Follow Bot")
        self.root.geometry("500x500")

        self.accounts_label = tk.Label(root, text="Accounts (username:password):")
        self.accounts_label.pack()
        self.accounts_text = tk.Text(root, height=10)
        self.accounts_text.pack()

        self.target_label = tk.Label(root, text="Account to Follow:")
        self.target_label.pack()
        self.target_entry = tk.Entry(root, width=50)
        self.target_entry.pack()

        self.threads_label = tk.Label(root, text="Number of Threads:")
        self.threads_label.pack()
        self.threads_entry = tk.Entry(root)
        self.threads_entry.pack()

        self.start_button = tk.Button(root, text="Start Following", command=self.start_following)
        self.start_button.pack(pady=10)

        self.log_text = tk.Text(root, height=10)
        self.log_text.pack()

        self.is_running = False

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        print(message)

    def create_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-extensions")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver

    def twitter_login(self, driver, username, password):
        driver.get("https://twitter.com/i/flow/login")
        wait = WebDriverWait(driver, 40)

        try:
            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
            username_field.send_keys(username)
            time.sleep(random.uniform(1, 3))
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[role="button"].r-13qz1uu')))
            next_button.click()

            password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
            password_field.send_keys(password)
            time.sleep(random.uniform(1, 3))
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid*="LoginForm_Login_Button"]')))
            login_button.click()
        except Exception as e:
            self.log(f"Error during login: {e}")
            return False

        # Verify login success
        try:
            home_icon = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
        except:
            self.log("Failed to login: Home icon not found")
            return False
        
        return True

    def follow_account(self, driver, account_to_follow):
        wait = WebDriverWait(driver, 40)
        try:
            driver.get(f"https://twitter.com/{account_to_follow}")
            time.sleep(5)
            follow_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@data-testid="placementTracking"]//span[text()="Follow"]')))
            follow_button.click()
            time.sleep(random.uniform(2, 4))
            self.log(f"Followed {account_to_follow} successfully!")
            return True
        except Exception as e:
            self.log(f"Failed to follow {account_to_follow}: {e}")
            return False

    def start_following(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Following process is already running.")
            return

        accounts = self.accounts_text.get("1.0", tk.END).strip().split("\n")
        accounts = [tuple(account.split(":")) for account in accounts if ":" in account]
        account_to_follow = self.target_entry.get().strip()
        num_threads = int(self.threads_entry.get())

        if not accounts or not account_to_follow or not num_threads:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        self.is_running = True
        threading.Thread(target=self.run_following, args=(accounts, account_to_follow, num_threads)).start()

    def run_following(self, accounts, account_to_follow, num_threads):
        total_tasks = len(accounts)
        completed_tasks = 0

        def run_thread(account):
            nonlocal completed_tasks
            self.log(f"Logging in with {account[0]}...")
            driver = self.create_driver()
            try:
                success = self.twitter_login(driver, account[0], account[1])
                if success:
                    self.log(f"Logged in successfully with {account[0]}.")
                    self.follow_account(driver, account_to_follow)
                else:
                    self.log(f"Failed to login with {account[0]}.")
            except Exception as e:
                self.log(f"Error with {account[0]}: {e}")
            finally:
                driver.quit()
                completed_tasks += 1
                self.log(f"Completed {completed_tasks}/{total_tasks} tasks.")
                time.sleep(random.uniform(2, 5))  # Add wait time to avoid rate limiting

        threads = []
        for account in accounts:
            if not self.is_running:
                break
            if len(threads) >= num_threads:
                for thread in threads:
                    thread.join()
                threads = []
            thread = threading.Thread(target=run_thread, args=(account,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.is_running = False
        self.log("All follow tasks completed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TwitterFollowBot(root)
    root.mainloop()
