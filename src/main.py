import customtkinter as ctk
import finnhub
import threading
import time
import json
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API Key Not Found!")

class StockTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PiTrader")
        self.geometry("480x320")
        self.attributes('-fullscreen', False)
        
        self.bg_primary = "#0a0e27"
        self.bg_card = "#1a2332"
        self.accent_green = "#00ff88"
        self.accent_red = "#ff4757"
        self.text_primary = "#ffffff"
        self.text_secondary = "#8892b0"
        self.configure(fg_color=self.bg_primary)
        self.client = finnhub.Client(api_key=API_KEY)
        self.symbols = self.load_portfolio()
        self.stock_frames = {}
        self.running = True
        self.show_add_section = False
        self.create_widgets()
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_portfolio(self):
        try:
            with open('portfolio.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default = ["AAPL", "MSFT", "AMZN", "GOOGL"]
            self.save_portfolio_list(default)
            return default
        except Exception as e:
            print(f"Error loading portfolio: {e}")
            return ["AAPL", "MSFT", "AMZN", "GOOGL"]
    
    def save_portfolio_list(self, portfolio_list):
        try:
            with open('portfolio.json', 'w') as f:
                json.dump(portfolio_list, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
    
    def save_portfolio(self):
        self.save_portfolio_list(self.symbols)
    
    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=8, padx=10, fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="PiTrader",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.text_primary
        )
        title_label.pack(side="left",pady=5, padx=5)
        
        self.last_updated_label = ctk.CTkLabel(
            header_frame,
            text="Last Updated: --:--",
            font=ctk.CTkFont(size=10),
            text_color=self.accent_green
        )
        self.last_updated_label.pack(side="left", padx=(5, 0))
        
        stats_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        stats_frame.pack(side="right")
        
        self.gainers_stat = ctk.CTkLabel(
            stats_frame,
            text="↑0",
            font=ctk.CTkFont(size=16),
            text_color=self.accent_green
        )
        self.gainers_stat.pack(side="left", padx=4)
        
        self.losers_stat = ctk.CTkLabel(
            stats_frame,
            text="↓0",
            font=ctk.CTkFont(size=16),
            text_color=self.accent_red
        )
        self.losers_stat.pack(side="left", padx=4)
        
        self.edit_btn = ctk.CTkButton(
            stats_frame,
            text="+",
            command=self.toggle_add_section,
            width=30,
            height=24,
            font=ctk.CTkFont(size=14),
            fg_color=self.bg_card,
            hover_color="#2a3447",
            corner_radius=4
        )
        self.edit_btn.pack(side="left", padx=(8, 0))
        
        self.add_frame = ctk.CTkFrame(self, fg_color=self.bg_card, corner_radius=6)
        
        add_inner = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        add_inner.pack(pady=8, padx=10, fill="x")
        
        self.symbol_entry = ctk.CTkEntry(
            add_inner,
            placeholder_text="Ticker...",
            width=100,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=self.bg_primary,
            corner_radius=4
        )
        self.symbol_entry.pack(side="left", padx=(0, 6))
        self.symbol_entry.bind("<Return>", lambda e: self.add_symbol())
        
        add_btn = ctk.CTkButton(
            add_inner,
            text="Add",
            command=self.add_symbol,
            width=50,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=self.accent_green,
            text_color="#000000",
            hover_color="#00cc6f",
            corner_radius=4
        )
        add_btn.pack(side="left")
        
        self.stocks_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#2a3447",
            scrollbar_button_hover_color="#3a4557"
        )
        self.stocks_frame.pack(pady=(5, 5), padx=10, fill="both", expand=True)
        
        for symbol in self.symbols:
            self.create_stock_frame(symbol)
    
    def toggle_add_section(self):
        self.show_add_section = not self.show_add_section
        if self.show_add_section:
            self.add_frame.pack(pady=(0, 5), padx=10, fill="x", after=self.edit_btn.master.master)
            self.symbol_entry.focus()
        else:
            self.add_frame.pack_forget()
    
    def create_stock_frame(self, symbol):
        frame = ctk.CTkFrame(
            self.stocks_frame,
            fg_color=self.bg_card,
            corner_radius=6,
            border_width=1,
            border_color="#2a3447"
        )
        frame.pack(pady=3, fill="x")
        
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(pady=8, padx=10, fill="x")
        
        remove_btn = ctk.CTkButton(
            inner,
            text="✕",
            command=lambda: self.remove_symbol(symbol),
            width=20,
            height=20,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=self.accent_red,
            corner_radius=3
        )
        remove_btn.place(relx=1.0, rely=0, anchor="ne")
        
        left_section = ctk.CTkFrame(inner, fg_color="transparent")
        left_section.pack(side="left", fill="x", expand=True)
        
        symbol_label = ctk.CTkLabel(
            left_section,
            text=symbol,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.text_secondary,
            anchor="w"
        )
        symbol_label.pack(anchor="w")
        
        price_label = ctk.CTkLabel(
            left_section,
            text="--",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.text_primary,
            anchor="w"
        )
        price_label.pack(anchor="w")
        
        right_section = ctk.CTkFrame(inner, fg_color="transparent")
        right_section.pack(side="right", padx=(8, 0))
        
        change_label = ctk.CTkLabel(
            right_section,
            text="--",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.text_secondary,
            anchor="e"
        )
        change_label.pack(pady=0)
        
        self.stock_frames[symbol] = {
            'frame': frame,
            'price_label': price_label,
            'change_label': change_label
        }
    
    def add_symbol(self):
        symbol = self.symbol_entry.get().strip().upper()
        if symbol and symbol not in self.symbols:
            self.symbols.append(symbol)
            self.create_stock_frame(symbol)
            self.symbol_entry.delete(0, 'end')
            self.update_stock(symbol)
            self.update_stats()
            self.save_portfolio()
    
    def remove_symbol(self, symbol):
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            if symbol in self.stock_frames:
                self.stock_frames[symbol]['frame'].destroy()
                del self.stock_frames[symbol]
            self.update_stats()
            self.save_portfolio()
    
    def update_stock(self, symbol):
        try:
            quote = self.client.quote(symbol)
            current_price = quote["c"]
            prev_close = quote["pc"]
            
            if current_price == 0 and prev_close == 0:
                raise Exception("Invalid")
            
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            
            self.after(0, self.update_ui, symbol, current_price, change, change_pct)
        except Exception as e:
            self.after(0, self.update_ui_error, symbol, str(e))
    
    def update_ui(self, symbol, price, change, change_pct):
        if symbol in self.stock_frames:
            frames = self.stock_frames[symbol]
            
            is_positive = change >= 0
            color = self.accent_green if is_positive else self.accent_red
            
            if price < 10:
                price_text = f"${price:.3f}"
            else:
                price_text = f"${price:.2f}"
            frames['price_label'].configure(text=price_text, text_color=color)
            
            if abs(change) < 1:
                dollar_text = f"${abs(change):.3f}"
            else:
                dollar_text = f"${abs(change):.2f}"
            
            arrow = "▲" if is_positive else "▼"
            change_text = f"{arrow} {abs(change_pct):.1f}% {dollar_text}"
            frames['change_label'].configure(text=change_text, text_color=color)
    
    def update_ui_error(self, symbol, error):
        if symbol in self.stock_frames:
            frames = self.stock_frames[symbol]
            frames['price_label'].configure(text="INVALID", text_color=self.accent_red)
            frames['change_label'].configure(text="", text_color=self.text_secondary)
    
    def update_stats(self):
        gainers = 0
        losers = 0
        
        for symbol in self.symbols:
            if symbol in self.stock_frames:
                change_text = self.stock_frames[symbol]['change_label'].cget("text")
                if "▲" in change_text:
                    gainers += 1
                elif "▼" in change_text:
                    losers += 1
        
        self.gainers_stat.configure(text=f"↑{gainers}")
        self.losers_stat.configure(text=f"↓{losers}")
    
    def update_loop(self):
        while self.running:
            for symbol in self.symbols[:]:
                if symbol in self.stock_frames:
                    self.update_stock(symbol)
            
            current_time = datetime.now().strftime("%I:%M:%S %p")
            self.after(0, lambda: self.last_updated_label.configure(text=f"Last Updated: {current_time}"))
            self.after(0, self.update_stats)
            time.sleep(5)
    
    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = StockTrackerApp()
    app.mainloop()