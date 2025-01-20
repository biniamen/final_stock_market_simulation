import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ToastrService } from 'ngx-toastr';
import { MatTableDataSource } from '@angular/material/table';

interface Dividend {
  id: number;
  company: number;
  budget_year: number;
  dividend_ratio: string;       // e.g. "2.10"
  total_dividend_amount: string; // e.g. "2100.00"
  status: string;              // "Pending" or "Disbursed"
  distributions: DividendDistribution[];
}

interface DividendDistribution {
  id: number;
  user: string;     // username
  amount: string;   // e.g. "300.00"
  created_at: string;
}

@Component({
  selector: 'app-add-dividend-dialog',
  templateUrl: './add-dividend-dialog.component.html',
  styleUrls: ['./add-dividend-dialog.component.css']
})
export class AddDividendDialogComponent implements OnInit {
  /** Reactive form to create a new Dividend */
  dividendForm!: FormGroup;

  /** Sum of all weightedValue from the parent component's data */
  totalWeightedValue: number = 0;

  /** Current budget year (e.g. 2025) */
  currentYear: number = new Date().getFullYear();

  /** Columns to display for the current-year Dividend table */
  displayedColumns: string[] = [
    'id',
    'company',
    'budget_year',
    'dividend_ratio',
    'total_dividend_amount',
    'status',
    'actions'
  ];

  /** Data source for the current-year Dividend table */
  dataSource = new MatTableDataSource<Dividend>();

  /** Columns to display for distributions */
  displayedDistributionsColumns: string[] = [
    'id',
    'user',
    'amount',
    'created_at'
  ];
  distributionsDataSource = new MatTableDataSource<DividendDistribution>();

  /** Flag to indicate that a disbursement request is in progress */
  isDisburseLoading = false;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<AddDividendDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private toastr: ToastrService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    // Retrieve the totalWeightedValue passed from the parent
    this.totalWeightedValue = this.data.totalWeightedValue;

    // Build the reactive form
    this.dividendForm = this.fb.group({
      totalDividendValue: ['', [Validators.required, Validators.min(0.01)]],
      dividendRatio: [{ value: '', disabled: true }],
      budgetYear: [{ value: this.currentYear, disabled: true }]
    });

    // Whenever totalDividendValue changes, automatically compute dividendRatio
    this.dividendForm.get('totalDividendValue')?.valueChanges.subscribe(value => {
      if (value && this.totalWeightedValue > 0) {
        const ratio = (value / this.totalWeightedValue).toFixed(4);
        this.dividendForm.get('dividendRatio')?.setValue(ratio);
      } else {
        this.dividendForm.get('dividendRatio')?.setValue('');
      }
    });

    // Fetch the existing current-year Dividend (if any)
    this.fetchCurrentYearDividend();
  }

  /**
   * Fetch the current year's Dividend record from the backend.
   * Endpoint: GET /api/stocks/dividends/current-year/
   */
  fetchCurrentYearDividend(): void {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    this.http
      .get<Dividend>('http://127.0.0.1:8000/api/stocks/dividends/current-year/', { headers })
      .subscribe({
        next: (dividend) => {
          // We only get one Dividend for the current year, so show it in a table row
          this.dataSource.data = [dividend];

          // If distributions exist, load them into the distributions table
          if (dividend.distributions && dividend.distributions.length > 0) {
            this.distributionsDataSource.data = dividend.distributions;
          } else {
            this.distributionsDataSource.data = [];
          }
        },
        error: (err) => {
          if (err.status === 404) {
            // No current-year Dividend found => clear table
            this.dataSource.data = [];
            this.distributionsDataSource.data = [];
          } else {
            this.toastr.error('Failed to fetch current year Dividend info.', 'Error');
          }
        }
      });
  }

  /**
   * Submit the form to create a new Dividend (for the current year).
   * Endpoint: POST /api/stocks/dividends/
   */
  onSubmit(): void {
    if (this.dividendForm.invalid) return;

    const totalDividendValue = parseFloat(this.dividendForm.get('totalDividendValue')?.value);
    const companyId = this.data.companyId;

    const payload = {
      company: companyId,
      budget_year: this.currentYear,
      total_dividend_amount: totalDividendValue
      
      // The ratio is computed in the backend or from totalWeightedValue
    };

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    });

    this.http
      .post<Dividend>('http://127.0.0.1:8000/api/stocks/dividends/', payload, { headers })
      .subscribe({
        next: (newDividend) => {
          this.toastr.success('Dividend added successfully!', 'Success');
          // Refresh the table with the newly created Dividend
          this.fetchCurrentYearDividend();
          // Optionally close dialog: this.dialogRef.close(true);
        },
        error: (err) => {
          console.error('Error adding dividend:', err);
          if (err.error && err.error.detail) {
            this.toastr.error(err.error.detail, 'Error');
          } else {
            this.toastr.error('Failed to add dividend.', 'Error');
          }
        }
      });
  }

  /**
   * Disburse the existing Dividend to users.
   * Endpoint: POST /api/stocks/dividends/:dividendId/disburse/
   */
  onDisburse(dividendId: number): void {
    if (this.isDisburseLoading) return;
    this.isDisburseLoading = true;

    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
      this.toastr.error('No access token found. Please log in.', 'Error');
      this.isDisburseLoading = false;
      return;
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    });

    this.http
      .post<any>(`http://127.0.0.1:8000/api/stocks/dividends/${dividendId}/disburse/`, {}, { headers })
      .subscribe({
        next: (resp) => {
          this.toastr.success('Dividends disbursed successfully!', 'Success');
          // Refresh the table to see updated status and distributions
          this.fetchCurrentYearDividend();
          this.isDisburseLoading = false;
        },
        error: (err) => {
          console.error('Error disbursing dividends:', err);
          if (err.error && err.error.detail) {
            this.toastr.error(err.error.detail, 'Error');
          } else {
            this.toastr.error('Failed to disburse dividends.', 'Error');
          }
          this.isDisburseLoading = false;
        }
      });
  }

  /**
   * Close the dialog if the user clicks "Cancel".
   */
  onCancel(): void {
    this.dialogRef.close(false);
  }
}
