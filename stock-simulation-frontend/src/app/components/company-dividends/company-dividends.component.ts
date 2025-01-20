import { Component, OnInit, ViewChild, TemplateRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatTableDataSource } from '@angular/material/table';
import { MatSort } from '@angular/material/sort';
import { MatPaginator } from '@angular/material/paginator';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';

import { Dividend, DividendService } from '../../services/dividend.service';

@Component({
  selector: 'app-company-dividends',
  templateUrl: './company-dividends.component.html',
  styleUrls: ['./company-dividends.component.css'],
})
export class CompanyDividendsComponent implements OnInit {
  // Material Table and Data
  displayedColumns: string[] = [
    'id',
    'budget_year',
    'dividend_ratio',
    'total_dividend_amount',
    'status',
    'created_at',
  ];
  dataSource: MatTableDataSource<Dividend> = new MatTableDataSource<Dividend>();

  @ViewChild(MatSort, { static: true }) sort!: MatSort;
  @ViewChild(MatPaginator, { static: true }) paginator!: MatPaginator;

  // For Add Dividend dialog
  @ViewChild('addDividendDialog') addDividendDialog!: TemplateRef<any>;
  addDialogRef!: MatDialogRef<any>;

  // Company + Dividends
  companyId: number | undefined;
  dividends: Dividend[] = [];

  // Reactive Form for creating a new Dividend
  dividendForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private dividendService: DividendService,
    private dialog: MatDialog
  ) {
    // Initialize the form
    this.dividendForm = this.fb.group({
      budget_year: ['', Validators.required],
      dividend_ratio: ['', Validators.required],
      total_dividend_amount: ['', Validators.required],
    });
  }

  ngOnInit(): void {
    // Replace with logic to get the logged-in user’s company admin ID
    this.companyId = 123; // Example ID

    if (this.companyId) {
      this.loadDividends(this.companyId);
    }

    // Configure table sorting & pagination
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
  }

  // Fetch Dividends from the service
  loadDividends(companyId: number): void {
    this.dividendService.getDividends(companyId).subscribe({
      next: (data: Dividend[]) => {
        this.dividends = data;
        this.dataSource.data = data;
      },
      error: (err) => {
        console.error('Error fetching dividends:', err);
      },
    });
  }

  // ========== TABLE FILTERING (SEARCH) ==========

  applyFilter(event: Event): void {
    const filterValue = (event.target as HTMLInputElement).value.trim().toLowerCase();
    this.dataSource.filter = filterValue;
  }

  // ========== OPEN/CLOSE ADD DIVIDEND DIALOG ==========

  openAddDividendDialog(): void {
    // Reset form before opening dialog
    this.dividendForm.reset();
    this.addDialogRef = this.dialog.open(this.addDividendDialog, {
      width: '500px',
    });
  }

  closeDialog(): void {
    this.addDialogRef.close();
  }

  // ========== ADD NEW DIVIDEND ==========

  submitDividend(): void {
    if (!this.companyId) return;

    // Check for duplicate budget year (client-side check)
    const year = this.dividendForm.value.budget_year;
    const duplicate = this.dividends.some((d) => d.budget_year === year);
    if (duplicate) {
      alert('Adding the same budget year dividend is not allowed.');
      return;
    }

    const payload: Partial<Dividend> = {
      ...this.dividendForm.value,
      company: this.companyId,
    };

    this.dividendService.createDividend(payload).subscribe({
      next: (created: Dividend) => {
        // Refresh table data
        this.loadDividends(this.companyId!);
        this.closeDialog();
      },
      error: (err) => {
        console.error('Error creating dividend:', err);
      },
    });
  }
}
