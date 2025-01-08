import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { MatDialog } from '@angular/material/dialog';
import { ToastrService } from 'ngx-toastr';

interface Stock {
  current_price: any;
  id: number;
  ticker_symbol: string;
  total_shares: number;
  available_shares: number;
}

interface UserTrade {
  id: number;
  user: number;
  stock: number;
  quantity: number;
  price: string;
  trade_time: string;
}

@Component({
  selector: 'app-bid-order',
  templateUrl: './bid-order.component.html',
  styleUrls: ['./bid-order.component.css']
})
export class BidOrderComponent implements OnInit {
  @ViewChild('orderModal') orderModal!: TemplateRef<any>;

  token: string | null = null;
  userId: string | null = null;

  stocks: Stock[] = [];
  selectedStockId: number = 0;
  selectedStockSymbol: string = '';

  orderType: string = 'Market'; // 'Market' or 'Limit'
  action: string = 'Buy';       // 'Buy' or 'Sell'
  price: number | null = null;
  quantity: number | null = null;

  userOwnedQuantity: number = 0; // Owned shares of the selected stock
  averagePurchasePrice: number | null = null; // Average purchase price for the selected stock
  profitOrLoss: number | null = null; // Calculated profit/loss for Limit Sell

  constructor(private http: HttpClient, public dialog: MatDialog,  private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    this.token = localStorage.getItem('access_token');
    this.userId = localStorage.getItem('user_id');

    if (!this.token || !this.userId) {
      alert('You must be logged in.');
      return;
    }

    this.fetchStocks();
  }

  fetchStocks(): void {
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http.get<Stock[]>('http://localhost:8000/api/stocks/stocks/', { headers }).subscribe({
      next: (data) => {
        this.stocks = data;
      },
      error: (err) => {
        console.error('Error fetching stocks', err);
      }
    });
  }

  onStockChange(stockId: number): void {
    this.selectedStockId = stockId;
    const selected = this.stocks.find(s => s.id === stockId);
    this.selectedStockSymbol = selected ? selected.ticker_symbol : '';

    if (this.action === 'Sell' && this.selectedStockId > 0) {
      this.fetchUserTrades();
      this.fetchUserAveragePrice();
    } else {
      this.userOwnedQuantity = 0;
      this.averagePurchasePrice = null;
    }

    this.updateProfitOrLoss();
  }

  onActionChange(): void {
    if (this.action === 'Sell' && this.selectedStockId > 0) {
      this.fetchUserTrades();
      this.fetchUserAveragePrice();
    } else {
      this.userOwnedQuantity = 0;
      this.averagePurchasePrice = null;
      this.profitOrLoss = null;
    }

    this.updateProfitOrLoss();
  }

  onOrderTypeChange(): void {
    this.updateProfitOrLoss();
  }

  onPriceChange(): void {
    this.updateProfitOrLoss();
  }

  onQuantityChange(): void {
    this.updateProfitOrLoss();
  }

  fetchUserTrades(): void {
    if (!this.userId) return;

    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    this.http.get<UserTrade[]>(`http://localhost:8000/api/stocks/user/${this.userId}/trades/`, { headers })
      .subscribe({
        next: (trades) => {
          const stockTrades = trades.filter(t => t.stock === this.selectedStockId);
          let totalQuantity = 0;
          for (const trade of stockTrades) {
            totalQuantity += trade.quantity;
          }
          this.userOwnedQuantity = totalQuantity;
          this.updateProfitOrLoss();
        },
        error: (err) => {
          console.error('Error fetching user trades', err);
        }
      });
  }

  fetchUserAveragePrice(): void {
    if (!this.userId || this.selectedStockId === 0) return;

    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
    });

    // Example endpoint: GET /api/stocks/user/<user_id>/portfolio/<stock_id>/
    // Returns: { "average_purchase_price": 100.00 }
    this.http.get<{average_purchase_price: number}>(`http://localhost:8000/api/stocks/user/${this.userId}/portfolio/${this.selectedStockId}/`, { headers })
      .subscribe({
        next: (data) => {
          this.averagePurchasePrice = data.average_purchase_price;
          this.updateProfitOrLoss();
        },
        error: (err) => {
          console.error('Error fetching user portfolio data', err);
        }
      });
  }

  updateProfitOrLoss(): void {
    // Calculate profit/loss only if:
    // action = Sell, orderType = Limit, price and quantity and averagePurchasePrice are available
    if (this.action === 'Sell' && this.orderType === 'Limit' && this.price && this.quantity && this.averagePurchasePrice !== null) {
      this.profitOrLoss = (this.price - this.averagePurchasePrice) * this.quantity;
    } else {
      this.profitOrLoss = null;
    }
  }

  canPlaceOrder(): boolean {
    // If selling, ensure quantity <= userOwnedQuantity
    if (this.action === 'Sell' && this.quantity && this.quantity > this.userOwnedQuantity) {
      return false;
    }

    // If limit order, price must be defined
    if (this.orderType === 'Limit' && !this.price) {
      return false;
    }

    // Ensure mandatory fields
    if (!this.userId || this.selectedStockId === 0 || !this.selectedStockSymbol || !this.quantity) {
      return false;
    }

    return true;
  }

  openOrderModal(): void {
    this.dialog.open(this.orderModal, { width: '500px' });
  }

  placeOrder(): void {
    if (!this.canPlaceOrder()) {
      alert("Invalid order details.");
      return;
    }
  
    const payload: any = {
      user: parseInt(this.userId!, 10),
      stock: this.selectedStockId,
      stock_symbol: this.selectedStockSymbol,
      order_type: this.orderType,
      action: this.action,
      quantity: this.quantity
    };
  
    // If Market order, use the stock's current price
    if (this.orderType === 'Market') {
      const selectedStock = this.stocks.find(s => s.id === this.selectedStockId);
      const currentStockPrice = selectedStock ? selectedStock.current_price : 0;
      payload.price = currentStockPrice;
    } else {
      // Limit orders require a user-specified price
      if (!this.price) {
        alert('Price is required for a Limit order.');
        return;
      }
      payload.price = this.price;
    }
  
    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    });
  
    this.http.post('http://localhost:8000/api/stocks/orders/', payload, { headers })
      .subscribe({
        next: (response: any) => {
          // Show the actual message from backend
          this.toastr.success(response.message, 'Order Placed');
          // Then close the modal
          this.dialog.closeAll();
        },
        error: (err: HttpErrorResponse) => {
          console.error('Error placing order:', err);
    
          let message = 'Failed to place the order.';
          
          // 1) If DRF returned "detail" key
          if (err.error && typeof err.error.detail === 'string') {
            message = err.error.detail;
          }
          // 2) If field-level errors (e.g., { "quantity": ["This field is required."] })
          else if (err.error && typeof err.error === 'object') {
            const fieldErrors = [];
            for (const key of Object.keys(err.error)) {
              fieldErrors.push(`${key}: ${err.error[key]}`);
            }
            if (fieldErrors.length > 0) {
              message = fieldErrors.join('\n');
            }
          }
    
          // Use Toastr to show the error
          this.toastr.error(message, 'Order Error');
          // Optionally close the modal
          this.dialog.closeAll();
        }
      });
}
}
