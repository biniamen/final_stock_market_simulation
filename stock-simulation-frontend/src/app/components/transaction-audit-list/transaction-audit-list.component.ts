// transaction-audit-list.component.ts

import { Component, OnInit } from '@angular/core';
import { PageEvent } from '@angular/material/paginator';
import { TransactionAuditService } from '../../services/transaction-audit.service';
import { ITransactionAuditTrail, DetailsObject } from '../../models/transaction-audit.model';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-transaction-audit-list',
  templateUrl: './transaction-audit-list.component.html',
  styleUrls: ['./transaction-audit-list.component.css']
})
export class TransactionAuditListComponent implements OnInit {
  /**
   * Raw data from the server.
   */
  rawData: ITransactionAuditTrail[] = [];

  /**
   * Data displayed on the current page only.
   */
  displayData: ITransactionAuditTrail[] = [];

  /**
   * Pagination properties.
   */
  pageSize = 5;
  currentPage = 0;
  totalRecords = 0;

  isLoading = false;
  errorMessage = '';

  constructor(
    private transactionAuditService: TransactionAuditService,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    this.fetchAuditTrails();
  }

  fetchAuditTrails(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.transactionAuditService.getAllAuditTrails().subscribe({
      next: (data: ITransactionAuditTrail[]) => {
        this.rawData = data;
        this.totalRecords = data.length;
        // Show only the first page of data:
        this.updateDisplayedData();
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Error fetching audit trails:', err);
        this.toastr.error('Failed to load audit trails.', 'Error');
        this.errorMessage = 'Failed to load audit trails.';
        this.isLoading = false;
      }
    });
  }

  /**
   * Updates the subset of data based on the current page and page size.
   */
  updateDisplayedData(): void {
    const startIndex = this.currentPage * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    this.displayData = this.rawData.slice(startIndex, endIndex);
  }

  /**
   * When the paginator changes, update currentPage and pageSize, then slice the array.
   */
  onPageChange(event: PageEvent): void {
    this.pageSize = event.pageSize;
    this.currentPage = event.pageIndex;
    this.updateDisplayedData();
  }

  /**
   * Check if 'details' is an object (so we can list each key-value pair).
   */
  isDetailsObject(details: string | DetailsObject | undefined): details is DetailsObject {
    return details !== null && typeof details === 'object';
  }

  /**
   * Convert the details object to a list of key/value pairs for easy display,
   * excluding any keys related to 'id'.
   */
  getDetailKeyValuePairs(details: string | DetailsObject): { key: string; value: any }[] {
    if (typeof details === 'string') {
      return [{ key: 'Details', value: details }];
    }

    // Convert each field in the object, excluding 'id' fields
    return Object.entries(details)
      .filter(([key, _]) => !this.isIdField(key))
      .map(([key, value]) => ({
        key: this.formatKey(key),
        value
      }));
  }

  /**
   * Determines if a given key is related to 'id'.
   * Excludes keys that are exactly 'id' or contain '_id'.
   * @param key The key to check.
   */
  private isIdField(key: string): boolean {
    const lowerKey = key.toLowerCase();
    return lowerKey === 'id' || lowerKey.endsWith('_id');
  }

  /**
   * Formats the key to make it more readable (e.g., snake_case to Title Case)
   * @param key The original key from the details object.
   */
  private formatKey(key: string): string {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }
}
