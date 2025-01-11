// src/app/components/transaction-audit-list/transaction-audit-list.component.ts

import { Component, OnInit, ViewChild } from '@angular/core';
import { TransactionAuditService } from '../../services/transaction-audit.service';
import { ITransactionAuditTrail, DetailsObject } from '../../models/transaction-audit.model';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';

@Component({
  selector: 'app-transaction-audit-list',
  templateUrl: './transaction-audit-list.component.html',
  styleUrls: ['./transaction-audit-list.component.css']
})
export class TransactionAuditListComponent implements OnInit {
  // Columns to display in the main table
  displayedColumns: string[] = ['event_type', 'timestamp', 'actions'];

  // Data source for the table
  dataSource = new MatTableDataSource<ITransactionAuditTrail>([]);
  isLoading = true;
  totalRecords = 0;
  pageSize = 10;
  currentPage = 1;
  expandedElement: ITransactionAuditTrail | null = null;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(private transactionAuditService: TransactionAuditService) {}

  ngOnInit(): void {
    this.fetchAuditTrails();
  }

  /**
   * Fetches audit trails from the backend service and populates the table.
   */
  fetchAuditTrails(): void {
    this.isLoading = true;
    this.transactionAuditService.getAllAuditTrails().subscribe({
      next: (data: ITransactionAuditTrail[]) => {
        this.dataSource.data = data;
        this.totalRecords = data.length;
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
        this.isLoading = false;
      },
      error: (err: any) => { // Explicitly type 'err'
        console.error('Error fetching audit trails:', err);
        this.dataSource.data = [];
        this.isLoading = false;
      }
    });
  }

  /**
   * Handles pagination changes.
   */
  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize;
    this.currentPage = event.pageIndex + 1;
    // Client-side pagination is already handled by MatTableDataSource
  }

  /**
   * Handles sorting changes.
   */
  onSortChange(sortState: Sort): void {
    // Sorting is handled automatically by MatTableDataSource
  }

  /**
   * Toggles the expansion of a row to show/hide details.
   */
  toggleRow(element: ITransactionAuditTrail): void {
    this.expandedElement = this.expandedElement === element ? null : element;
  }

  /**
   * Determines whether a row is a detail row.
   */
  isExpansionDetailRow = (index: number, row: any): boolean => {
    return this.expandedElement === row;
  }

  /**
   * Checks if the details field is an object.
   */
  isDetailsObject(details: string | DetailsObject | undefined): details is DetailsObject {
    return typeof details === 'object' && details !== null;
  }

  /**
   * Converts the details object into a list of key-value pairs for display.
   */
  getDetailKeyValuePairs(details: string | DetailsObject): { key: string; value: any }[] {
    if (typeof details === 'string') {
      return [{ key: 'Details', value: details }];
    }

    const fieldsToShow: (keyof DetailsObject)[] = [
      'buyer_id',
      'buyer_username',
      'price_per_share',
      'quantity',
      'remaining_quantity',
      'seller_id',
      'seller_username',
      'stock_id',
      'stock_symbol',
      'total_cost',
      'trade_type',
      'transaction_fee'
    ];

    return fieldsToShow
      .filter(field => details[field] !== undefined)
      .map(field => ({
        key: this.formatKey(field),
        value: details[field]
      }));
  }

  /**
   * Formats the key for display (e.g., 'buyer_id' -> 'Buyer Id').
   */
  private formatKey(key: string): string {
    return key.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  }

  /**
   * Exports the table data to a CSV file.
   */
  exportToCSV(): void {
    if (!this.dataSource.data.length) {
      console.warn('No data available to export.');
      return;
    }

    const csvRows = this.dataSource.data.map(row => {
      const rowDetails = this.isDetailsObject(row.details)
        ? JSON.stringify(row.details)
        : row.details;
      return {
        EventType: row.event_type,
        Timestamp: row.timestamp,
        Details: rowDetails ?? 'N/A'
      };
    });

    const header = Object.keys(csvRows[0]).join(',');
    const body = csvRows.map(row => Object.values(row).map(val => `"${val}"`).join(',')).join('\n');
    const csvContent = `data:text/csv;charset=utf-8,${header}\n${body}`;
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'audit_trails.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Prints the table data.
   */
  printTable(): void {
    if (!this.dataSource.data.length) {
      console.warn('No data available to print.');
      return;
    }

    let tableRows = this.dataSource.data.map(row => {
      const eventType = row.event_type;
      const timestamp = new Date(row.timestamp).toLocaleString();
      let details: string;

      if (typeof row.details === 'string') {
        details = row.details;
      } else {
        details = `
Buyer Username: ${row.details.buyer_username || 'N/A'}
Price per Share: ${row.details.price_per_share || 'N/A'}
Quantity: ${row.details.quantity || 'N/A'}
Remaining Quantity: ${row.details.remaining_quantity || 'N/A'}
Seller Username: ${row.details.seller_username || 'N/A'}
Stock Symbol: ${row.details.stock_symbol || 'N/A'}
Total Cost: ${row.details.total_cost || 'N/A'}
Trade Type: ${row.details.trade_type || 'N/A'}
Transaction Fee: ${row.details.transaction_fee || 'N/A'}
        `;
      }

      return `
        <tr>
          <td>${eventType}</td>
          <td>${timestamp}</td>
          <td>${details}</td>
        </tr>
      `;
    }).join('');

    const printContents = `
      <div style="padding:20px;font-family:Arial,sans-serif;">
        <h1 style="text-align:center;">Transaction Audit Trails</h1>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <thead>
            <tr style="background-color:#f2f2f2;text-align:left;border-bottom:1px solid #ddd;">
              <th style="padding:10px;border:1px solid #ddd;">Event Type</th>
              <th style="padding:10px;border:1px solid #ddd;">Timestamp</th>
              <th style="padding:10px;border:1px solid #ddd;">Details</th>
            </tr>
          </thead>
          <tbody>
            ${tableRows}
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
