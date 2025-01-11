import { Component, OnInit, ViewChild } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';

@Component({
  selector: 'app-trades-with-order-info',
  templateUrl: './trades-with-order-info.component.html',
  styleUrls: ['./trades-with-order-info.component.css']
})
export class TradesWithOrderInfoComponent implements OnInit {
  displayedColumns: string[] = [
    'id',
    'stock_symbol',
    'order_type',
    'action',
    'price',
    'quantity',
    'transaction_fee',
    'total_buying_price', // New calculated column
    'trade_time',
  ];
  dataSource = new MatTableDataSource<any>([]);
  isLoading = true;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchTradesWithOrderInfo();
  }

  fetchTradesWithOrderInfo(): void {
    const userId = localStorage.getItem('user_id') || '123';
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    });

    this.http
      .get<any[]>(`http://127.0.0.1:8000/api/stocks/user/${userId}/trades_with_order_info/`, { headers })
      .subscribe(
        (data) => {
          // Add the calculated "Total Buying Price" to each row
          this.dataSource.data = data.map(row => ({
            ...row,
            total_buying_price: row.price * row.quantity
          }));
          this.dataSource.paginator = this.paginator;
          this.dataSource.sort = this.sort;
          this.isLoading = false;
        },
        (error) => {
          console.error('Error fetching trades with order info:', error);
          this.isLoading = false;
        }
      );
  }

  exportToCSV(): void {
    const csvData = this.dataSource.data.map(row => ({
      ID: row.id,
      StockSymbol: row.stock_symbol,
      OrderType: row.order_type,
      Action: row.action,
      Price: row.price,
      Quantity: row.quantity,
      TransactionFee: row.transaction_fee,
      TotalBuyingPrice: row.total_buying_price, // Include calculated value in CSV
      TradeTime: row.trade_time
    }));

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [
        Object.keys(csvData[0]).join(','), // Add headers
        ...csvData.map(row => Object.values(row).join(',')) // Add rows
      ].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'trades_with_order_info.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  printTable(): void {
    const printContents = `
      <div style="padding: 20px; font-family: Arial, sans-serif;">
        <h1 style="text-align: center;">Trades With Order Info</h1>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
          <thead>
            <tr style="background-color: #f2f2f2; text-align: left; border-bottom: 1px solid #ddd;">
              <th style="padding: 10px; border: 1px solid #ddd;">ID</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Stock Symbol</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Order Type</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Action</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Price</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Quantity</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Transaction Fee</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Total Buying Price</th>
              <th style="padding: 10px; border: 1px solid #ddd;">Trade Time</th>
            </tr>
          </thead>
          <tbody>
            ${this.dataSource.data.map((row) => `
              <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; border: 1px solid #ddd;">${row.id}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.stock_symbol}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.order_type}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.action}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.price}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.quantity}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.transaction_fee}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${row.total_buying_price}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">${new Date(row.trade_time).toLocaleString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    const originalContents = document.body.innerHTML;
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
  }
}
